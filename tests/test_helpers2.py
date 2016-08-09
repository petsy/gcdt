from nose.tools import assert_equal, assert_true, assert_in
from helpers import with_setup_args


# copy from the one in test_helpers.py
# to make sure that with_setup_args import works
def _setup2():
    return {'x': 42, 'foo': 10, 'my_bucket': []}


def _teardown2(foo, my_bucket, x):
    assert_equal(foo, 10)
    assert_equal(x, 42)
    assert_in('one', my_bucket)


def _teardown3(foo, my_bucket, x):
    assert_equal(foo, 10)
    assert_equal(x, 42)
    assert_in('two', my_bucket)


@with_setup_args(_setup2, _teardown2)
def test_with_setup_args2(foo, my_bucket, x):
    # !!!note this does not work => use kwargs!!!
    my_bucket.append('one')
    assert_equal(foo, 10)
    assert_equal(x, 42)
    return {'my_bucket': my_bucket}


@with_setup_args(_setup2, _teardown3)
def test_with_setup_args3(foo, **kwargs):
    kwargs['my_bucket'].append('two')  # use this way to
    assert_equal(foo, 10)
    assert_true('x' in kwargs)
    assert_equal(kwargs['x'], 42)
    return {'my_bucket': kwargs['my_bucket']}
