# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import os

from nose.tools import assert_equal, assert_true, assert_items_equal, \
    assert_is_not_none

from gcdt.tenkai_core import _make_tar_file, _files_to_bundle, bundle_revision, \
    _build_bundle_key

from .helpers import temp_folder  # fixtures!
from . import here


def test_make_tar_file(temp_folder):
    # _make_tar_file implements bundle
    codedeploy = here('resources/simple_codedeploy/codedeploy')
    file_suffix = os.getenv('BUILD_TAG', '')
    expected_filename = '%s/tenkai-bundle%s.tar.gz' % (temp_folder[0], file_suffix)

    tarfile_name = _make_tar_file(path=codedeploy,
                                  outputpath=temp_folder[0])
    assert_equal(tarfile_name, expected_filename)
    assert_true(os.path.isfile(expected_filename))


def test_bundle_revision(temp_folder):
    os.chdir(here('resources/simple_codedeploy'))
    file_suffix = os.getenv('BUILD_TAG', '')
    expected_filename = '%s/tenkai-bundle%s.tar.gz' % (temp_folder[0], file_suffix)

    tarfile_name = bundle_revision(outputpath=temp_folder[0])
    assert_equal(tarfile_name, expected_filename)
    assert_true(os.path.isfile(expected_filename))


def test_files_to_bundle():
    codedeploy = here('resources/simple_codedeploy/codedeploy')
    expected = ['sample_code2.txt', 'sample_code.txt', 'folder/sample_code3.txt']

    actual = [x[1] for x in _files_to_bundle(codedeploy)]
    assert_items_equal(actual, expected)


def test_build_bundle_key():
    application_name = 'sample_name'
    expected = '%s/bundle.tar.gz' % application_name
    assert_equal(_build_bundle_key(application_name), expected)
