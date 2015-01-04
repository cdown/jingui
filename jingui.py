#!/usr/bin/env python

from distutils.dir_util import mkpath
import subprocess
import errno
import random
import string
import os
import json
import uuid


class Jingui(object):
    def __init__(self, repo_dir=None):
        if repo_dir is None:
            self.repo_dir = os.path.expanduser('~/.jingui')
        else:
            self.repo_dir = repo_dir

        self.init_repo()

        self.map_file = os.path.join(self.repo_dir, 'map')
        self.map_file_contents = self.read_map_file()
        self.editor = self.determine_editor()

    def init_repo(self):
        mkpath(self.repo_dir, mode=0o100700)

    def hierarchy_to_string(self, hierarchy):
        return '/'.join(hierarchy)

    def determine_editor(self):
        for env in ['VISUAL', 'EDITOR']:
            if env in os.environ:
                return os.environ[env]
        return 'vi'

    def read_map_file(self):
        try:
            with open(self.map_file, 'r+') as f:
                map_file_contents = json.load(f)
        except IOError as e:
            if e.errno != errno.ENOENT:
                raise
            map_file_contents = {}

        return map_file_contents

    def save_map_file(self):
        with open(self.map_file, 'w+') as f:
            json.dump(self.map_file_contents, f)

    def add_to_map_file(self, hierarchy, path):
        # TODO: Behaviour on overwriting existing hierarchy?
        hier_str = self.hierarchy_to_string(hierarchy)
        self.map_file_contents[hier_str] = path

    def remove_from_map_file(self, hierarchy):
        del self.map_file_contents[self.hierarchy_to_string(hierarchy)]

    def get_path_from_hierarchy(self, hierarchy):
        return self.map_file_contents[self.hierarchy_to_string(hierarchy)]

    def cleanup(self):
        self.save_map_file()

    def absolute_path_to_file(self, path):
        return os.path.join(self.repo_dir, path)

    def random_password(self, length):
        return ''.join(
            random.SystemRandom().choice(
                string.ascii_letters + string.digits
            ) for _ in range(length)
        )

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

        abs_file_name = self.absolute_path_to_file(file_name)

        if generate:
            with open(abs_file_name, 'w+') as f:
                f.write('%s\n' % self.random_password(length))
        else:
            self.open_file_in_editor(abs_file_name)

        self.add_to_map_file(hierarchy, file_name)
        return file_name

    def remove_metadata_from_repo(self, hierarchy):
        path = self.get_path_from_hierarchy(hierarchy)
        self.remove_from_map_file(hierarchy)
        os.unlink(self.absolute_path_to_file(path))
        return path
