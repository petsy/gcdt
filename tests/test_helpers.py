import os
import shutil
from tempfile import mkdtemp

from nose.tools import assert_equal, assert_true, assert_in
from helpers import with_setup_args, create_tempfile, get_size


# code & sample from here:
# http://stackoverflow.com/questions/10565523/how-can-i-access-variables-set-in-the-python-nosetests-setup-function
#def _setup():
#    foo = 10
#    my_bucket = []
#    return [foo, my_bucket], {'x': 42}
def _setup():
    return {'x': 42, 'foo': 10, 'my_bucket': []}


def _teardown(foo, my_bucket, x):
    assert_equal(foo, 10)
    assert_equal(x, 42)
    assert_in('one', my_bucket)


@with_setup_args(_setup, _teardown)
def test_with_setup_args(foo, my_bucket, **kwargs):
    my_bucket.append('one')
    assert_equal(foo, 10)
    assert_true('x' in kwargs)
    assert_equal(kwargs['x'], 42)
    return {'my_bucket': my_bucket}


@with_setup_args(_setup, _teardown)
def test_with_setup_args4(foo, my_bucket, **kwargs):
    my_bucket.append('one')
    assert_equal(foo, 10)
    assert_true('x' in kwargs)
    assert_equal(kwargs['x'], 42)
    return {'my_bucket': my_bucket}


def test_create_tempfile():
    tf = create_tempfile('blah\nblub\n')
    with open(tf, 'r') as tfile:
        contents = tfile.read()
        assert_equal(contents, 'blah\nblub\n')
    # cleanup the tempfile
    os.unlink(tf)


def test_get_size():
    cwd = (os.getcwd())
    # prepare files for test
    folder = mkdtemp()
    os.chdir(folder)
    # prepare two files to read the size
    with open('tmp1.txt', 'w')as t1:
        t1.write('some\nstuff\n    \nhere\n')
    with open('tmp2.txt', 'w')as t2:
        t2.write('some\nmore stuff\n    \nhere\n')

    size = get_size()
    assert_equal(size, 47)

    # cleanup
    os.chdir(cwd)
    shutil.rmtree(folder)

# TODO: write test for check_preconditions!
