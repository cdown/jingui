#!/usr/bin/env python

from distutils.dir_util import mkpath
import subprocess
from subprocess import PIPE, STDOUT
import errno
import locale
import random
import string
import os
import json
import uuid
import gnupg


class GitError(Exception):
    pass


class Jingui(object):
    def __init__(self, repo_dir=None):
        self.gpg = gnupg.GPG()
        self.system_locale = locale.getdefaultlocale()[1]
        self.editor = self.determine_editor()

        if repo_dir is None:
            self.repo_dir = os.path.expanduser('~/.jingui')
        else:
            self.repo_dir = repo_dir

    def load_files(self):
        self.pgp_id_file = os.path.join(self.repo_dir, 'id')
        self.pgp_id = self.read_pgp_id_file()
        self.map_file = os.path.join(self.repo_dir, 'map')
        self.map_file_contents = self.read_map_file()

    def init_repo(self):
        mkpath(self.repo_dir, mode=0o100700)
        self.git(['init'])

    @staticmethod
    def hierarchy_to_string(hierarchy):
        return '/'.join(hierarchy)

    @staticmethod
    def determine_editor():
        for env in ['VISUAL', 'EDITOR']:
            if env in os.environ:
                return os.environ[env]
        return 'vi'

    def gpg_decrypt_from_file(self, enc_path):
        with open(enc_path) as enc_f:
            decrypted = self.gpg.decrypt_file(enc_f)
        return decrypted

    def gpg_encrypt_to_file(self, data, enc_path):
        encrypted = self.gpg.encrypt(data, self.pgp_id)
        with open(enc_path, 'wb+') as enc_f:
            enc_f.write(encrypted)

    def read_pgp_id_file(self):
        try:
            with open(self.pgp_id_file, 'r+') as pgp_id_f:
                return pgp_id_f.read()
        except IOError as exc:
            if exc.errno != errno.ENOENT:
                raise

    def read_map_file(self):
        try:
            decrypted = self.gpg_decrypt_from_file(self.map_file)
        except IOError as exc:
            if exc.errno != errno.ENOENT:
                raise
            map_file_contents = {}
        else:
            map_file_contents = json.loads(decrypted)

        return map_file_contents

    def save_map_file(self):
        map_contents_cleartext = json.dumps(self.map_file_contents)
        self.gpg_encrypt_to_file(map_contents_cleartext, self.map_file)

    def add_to_map_file(self, hierarchy, path, save=True):
        # TODO: Behaviour on overwriting existing hierarchy?
        hier_str = self.hierarchy_to_string(hierarchy)
        self.map_file_contents[hier_str] = path
        if save:
            self.save_map_file()

    def remove_from_map_file(self, hierarchy):
        del self.map_file_contents[self.hierarchy_to_string(hierarchy)]

    def get_path_from_hierarchy(self, hierarchy):
        return self.map_file_contents[self.hierarchy_to_string(hierarchy)]

    def cleanup(self):
        self.save_map_file()

    def relative_path_to_abs(self, path):
        return os.path.join(self.repo_dir, path)

    @staticmethod
    def random_password(length):
        return ''.join(
            random.SystemRandom().choice(
                string.ascii_letters + string.digits
            ) for _ in range(length)
        )

    def git(self, args):
        env = os.environ.copy()
        env.update({
            'GIT_WORK_TREE': self.repo_dir,
            'GIT_DIR': os.path.join(self.repo_dir, '.git'),
            'PAGER': 'cat',
        })

        try:
            stdout = subprocess.check_output(
                ['git'] + args, env=env, stderr=STDOUT,
            )
        except subprocess.CalledProcessError as err:
            raise GitError(err.output)

        return stdout.decode(self.system_locale)

    def git_commit_path_safe(self, path, msg=''):
        self.git(['reset', '.'])
        self.git(['add', self.map_file, path])
        self.git(['commit', '--allow-empty-message', '-m', msg])

    def git_remove_path_safe(self, path, msg=''):
        self.git(['reset', '.'])
        self.git(['add', self.map_file])
        self.git(['rm', path])
        self.git(['commit', '--allow-empty-message', '-m', msg])

    def open_file_in_editor(self, file_name):
        subprocess.check_call([self.editor, file_name])
        if not os.path.isfile(file_name):
            raise IOError('File was not written by your editor')

    def add_metadata_to_repo(self, hierarchy, generate=False, length=50):
        try:
            # Check if we already have a file for this hierarchy in the repo
            file_name = self.get_path_from_hierarchy(hierarchy)
        except KeyError:
            file_name = str(uuid.uuid4())

        abs_file_name = self.relative_path_to_abs(file_name)

        if generate:
            with open(abs_file_name, 'w+') as password_f:
                password_f.write('%s\n' % self.random_password(length))
        else:
            self.open_file_in_editor(abs_file_name)

        self.add_to_map_file(hierarchy, file_name)
        self.git_commit_path_safe(file_name)

        return file_name

    def remove_metadata_from_repo(self, hierarchy):
        path = self.get_path_from_hierarchy(hierarchy)
        self.remove_from_map_file(hierarchy)
        self.git_remove_path_safe(path)
        return path
