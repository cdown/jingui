#!/usr/bin/env python

import jingui
from nose.tools import eq_ as eq, ok_ as ok, assert_raises, raises
import tempfile
import os
import errno
import shutil
import subprocess
import stat
import unittest


class JinguiTests(unittest.TestCase):
    def setUp(self):
        repo_dir = tempfile.mkdtemp()
        os.rmdir(repo_dir)
        self.j = jingui.Jingui(repo_dir)
        self.j.init_repo()

    def tearDown(self):
        shutil.rmtree(self.j.repo_dir)

    def test_init_repo(self):
        mode = stat.S_IMODE(os.stat(self.j.repo_dir).st_mode)

        ok(os.path.isdir(self.j.repo_dir))
        eq(0o700, mode)

    def test_hierarchy_to_string(self):
        eq(
            'foo/bar/baz',
            self.j.hierarchy_to_string(['foo', 'bar', 'baz']),
        )

    def test_determine_editor_set_editor(self):
        del os.environ['VISUAL']
        os.environ['EDITOR'] = 'EDITOR'
        eq(
            'EDITOR',
            self.j.determine_editor(),
        )

    def test_determine_editor_set_visual_override(self):
        os.environ['VISUAL'] = 'VISUAL'
        os.environ['EDITOR'] = 'EDITOR'
        eq(
            'VISUAL',
            self.j.determine_editor(),
        )

    def test_determine_editor_unset(self):
        del os.environ['VISUAL']
        del os.environ['EDITOR']
        eq(
            'vi',
            self.j.determine_editor(),
        )

    def test_read_map_file_none_exists(self):
        # There's no map file by default since we get a fresh repo in every
        # test
        eq(
            {},
            self.j.read_map_file(),
        )

    def test_read_map_file_exists(self):
        self.j.add_to_map_file(['foo'], 'bar')
        self.j.save_map_file()

        eq(
            {'foo': 'bar'},
            self.j.read_map_file(),
        )

    def test_read_map_file_is_a_dir_not_silenced(self):
        os.mkdir(self.j.map_file)

        with assert_raises(IOError) as cm:
            self.j.read_map_file()

        eq(errno.EISDIR, cm.exception.errno)

    def test_save_map_file(self):
        # Already tested by test_read_map_file_exists()
        pass

    def test_add_to_map_file_single(self):
        # Already tested by test_read_map_file_exists()
        pass

    def test_add_to_map_file_multiple(self):
        self.j.add_to_map_file(['foo'], 'bar')
        self.j.add_to_map_file(['baz', 'qux'], 'wibble')

        eq(
            {
                'foo': 'bar',
                'baz/qux': 'wibble',
            },
            self.j.map_file_contents,
        )

    def test_add_to_map_file_existing_overwrite(self):
        self.j.add_to_map_file(['foo'], 'bar')
        self.j.add_to_map_file(['foo'], 'baz')

        eq(
            {'foo': 'baz'},
            self.j.map_file_contents,
        )

    def test_remove_from_map_file_exists(self):
        self.j.add_to_map_file(['foo', 'bar'], 'baz')
        self.j.add_to_map_file(['wibble', 'wobble'], 'jelly')
        self.j.remove_from_map_file(['foo', 'bar'])

        eq(
            {'wibble/wobble': 'jelly'},
            self.j.map_file_contents,
        )

    @raises(KeyError)
    def test_remove_from_map_file_not_exist(self):
        self.j.remove_from_map_file(['foo', 'bar'])

    def test_get_path_from_hierarchy(self):
        self.j.add_to_map_file(['foo', 'bar'], 'baz')
        eq('baz', self.j.get_path_from_hierarchy(['foo', 'bar']))

    def test_cleanup_map_file_is_saved(self):
        self.j.add_to_map_file(['foo', 'bar'], 'baz')
        self.j.add_to_map_file(['wibble', 'wobble'], 'jelly')

        eq({}, self.j.read_map_file())

        self.j.cleanup()

        eq(
            {
                'foo/bar': 'baz',
                'wibble/wobble': 'jelly'
            },
            self.j.read_map_file(),
        )

    def test_absolute_path_to_file(self):
        eq(
            os.path.join(self.j.repo_dir, 'foo'),
            self.j.absolute_path_to_file('foo'),
        )

    def test_add_metadata_to_repo(self):
        file_name = self.j.add_metadata_to_repo(['foo', 'bar'], generate=True)

        eq(
            {
                'foo/bar': file_name,
            },
            self.j.map_file_contents,
        )

        ok(os.path.isfile(self.j.absolute_path_to_file(file_name)))

    def test_add_metadata_to_repo_same_hierarchy_same_file(self):
        path_1 = self.j.add_metadata_to_repo(['foo', 'bar'], generate=True)
        path_2 = self.j.add_metadata_to_repo(['foo', 'bar'], generate=True)

        eq(path_1, path_2)

    def test_add_metadata_to_repo_editor_did_not_create(self):
        self.j.editor = 'true'
        assert_raises(IOError, self.j.add_metadata_to_repo, ['foo', 'bar'])

    def test_add_metadata_to_repo_editor_failure_is_raised(self):
        self.j.editor = 'false'
        assert_raises(
            subprocess.CalledProcessError,
            self.j.add_metadata_to_repo,
            ['foo', 'bar'],
        )

    def test_random_password_length(self):
        eq(1024, len(self.j.random_password(1024)))

    def test_remove_metadata_from_repo(self):
        in_file = self.j.add_metadata_to_repo(['foo', 'bar'], generate=True)
        out_file = self.j.remove_metadata_from_repo(['foo', 'bar'])

        eq(in_file, out_file)
        ok(not os.path.exists(self.j.absolute_path_to_file(in_file)))
