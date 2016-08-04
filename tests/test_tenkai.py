from nose.tools import assert_equal, assert_true, assert_items_equal
import nose
import os
import shutil
from tempfile import mkdtemp
from gcdt.tenkai_core import _make_tar_file, _files_to_bundle, bundle_revision, \
    _build_bundle_key


def here(p): return os.path.join(os.path.dirname(__file__), p)


def test_make_tar_file():
    # _make_tar_file implements bundle
    codedeploy = here('resources/simple_codedeploy/codedeploy')
    folder = mkdtemp()
    expected_filename = '%s/tenkai-bundle.tar.gz' % folder

    tarfile_name = _make_tar_file(path=codedeploy,
                                  outputpath=folder)
    assert_equal(tarfile_name, expected_filename)
    assert_true(os.path.isfile(expected_filename))

    # cleanup
    shutil.rmtree(folder)


def test_bundle_revision():
    cwd = (os.getcwd())
    os.chdir(here('resources/simple_codedeploy'))
    folder = mkdtemp()
    expected_filename = '%s/tenkai-bundle.tar.gz' % folder

    tarfile_name = bundle_revision(outputpath=folder)
    assert_equal(tarfile_name, expected_filename)
    assert_true(os.path.isfile(expected_filename))

    # cleanup
    os.chdir(cwd)
    shutil.rmtree(folder)


def test_files_to_bundle():
    codedeploy = here('resources/simple_codedeploy/codedeploy')
    expected = ['sample_code2.txt', 'sample_code.txt', 'folder/sample_code3.txt']

    actual = [x[1] for x in _files_to_bundle(codedeploy)]
    assert_items_equal(actual, expected)


def test_build_bundle_key():
    application_name = 'sample_name'
    expected = '%s/bundle.tar.gz' % application_name
    assert_equal(_build_bundle_key(application_name), expected)
