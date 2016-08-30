# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import six
from collections import deque
import random
import string
from tempfile import NamedTemporaryFile
from nose.plugins.skip import SkipTest


def with_setup_args(setup, teardown=None):
    """Decorator to add setup and/or teardown methods to a test function::
      @with_setup_args(setup, teardown)
      def test_something():
          " ... "
    The setup function should return (args, kwargs) which will be passed to
    test function, and teardown function.
    Note that `with_setup_args` is useful *only* for test functions, not for test
    methods or inside of TestCase subclasses.

    code & sample from here:
    http://stackoverflow.com/questions/10565523/how-can-i-access-variables-set-in-the-python-nosetests-setup-function

    def setup():
        foo = 10
        return [foo], {}

    def teardown(foo):
        pass

    @with_setup_args(setup, teardown)
    def test_foo_value(foo):
        nose.tools.assert_equal(foo, 10)
    """

    def decorate(func):
        kwargs = {}

        def test_wrapped():
            k = func(**kwargs)
            if k:
                kwargs.update(k)

        test_wrapped.__name__ = func.__name__

        def setup_wrapped():
            k = setup()
            kwargs.update(k)
            if hasattr(func, 'setup'):
                func.setup()
        test_wrapped.setup = setup_wrapped

        if teardown:
            def teardown_wrapped():
                if hasattr(func, 'teardown'):
                    func.teardown()
                teardown(**kwargs)

            test_wrapped.teardown = teardown_wrapped
        else:
            if hasattr(func, 'teardown'):
                test_wrapped.teardown = func.teardown()
        return test_wrapped
    return decorate


def create_tempfile(contents):
    """Helper to create a named tempoary file with contents.
    Note: caller has responsibility to clean up the temp file!

    :param contents: define the contents of the tempoary file
    :return: filename of the tempoary file
    """

    # helper to create a named temp file
    tf = NamedTemporaryFile(delete=False)
    with open(tf.name, 'w') as tfile:
        tfile.write(contents)

    return tf.name


def get_size(start_path='.'):
    """Accumulate the size of the files in the folder.

    :param start_path:
    :return: size
    """
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size


def check_preconditions():
    """Make sure the default AWS profile is set so the test can run on AWS."""
    if os.getenv('USER', None) != 'jenkins' and \
            not os.getenv('AWS_DEFAULT_PROFILE', None):
        # http://stackoverflow.com/questions/1120148/disabling-python-nosetests/1843106
        print("AWS_DEFAULT_PROFILE variable not set! Test is skipped.")
        raise SkipTest("AWS_DEFAULT_PROFILE variable not set! Test is skipped.")
    # export AWS_DEFAULT_PROFILE=superuser-qa-dev => README.md
    if not os.getenv('ENV', None):
        print("ENV environment variable not set! Test is skipped.")
        raise SkipTest("ENV environment variable not set! Test is skipped.")
    if not os.getenv('ACCOUNT', None):
        print("ACCOUNT environment variable not set! Test is skipped.")
        raise SkipTest("ACCOUNT environment variable not set! Test is skipped.")


def random_string():
    """Create a random 6 character string.
    """
    return ''.join([random.choice(string.ascii_lowercase) for i in xrange(6)])


'''
class FakeSocket(object):
    """ A fake socket for testing datadog statsd. """

    def __init__(self):
        self.payloads = deque()

    def send(self, payload):
        assert type(payload) == six.binary_type
        self.payloads.append(payload)

    def recv(self):
        try:
            return self.payloads.popleft().decode('utf-8')
        except IndexError:
            return None

    def __repr__(self):
        return str(self.payloads)
'''
