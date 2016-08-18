# -*- coding: utf-8 -*-
from nose.tools import assert_equal
from StringIO import StringIO
from gcdt.utils import version, __version__, retries


def test_version():
    out = StringIO()
    version(out=out)
    assert_equal(out.getvalue().strip(), 'gcdt version %s' % __version__)


def test_retries_backoff():
    state = {'r': 0, 'h': 0, 'backoff': 2, 'tries': 5, 'mydelay': 0.1}

    def a_hook(tries_remaining, e, delay):
        assert_equal(tries_remaining, state['tries'] - state['r'])
        assert_equal(e.message, 'test retries!')
        assert_equal(delay, state['mydelay'])
        state['mydelay'] *= state['backoff']
        state['h'] += 1

    @retries(state['tries'], delay=0.1, backoff=state['backoff'], hook=a_hook)
    def works_after_four_tries():
        state['r'] += 1
        if state['r'] < 5:
            raise Exception('test retries!')

    works_after_four_tries()
    assert_equal(state['r'], 5)


def test_retries_until_it_works():
    state = {'r': 0, 'h': 0}

    def a_hook(tries_remaining, e, delay):
        state['h'] += 1

    @retries(20, delay=0, exceptions=(ZeroDivisionError,), hook=a_hook)
    def works_after_four_tries():
        state['r'] += 1
        if state['r'] < 5:
            x = 5/0

    works_after_four_tries()
    assert_equal(state['r'], 5)
    assert_equal(state['h'], 4)


def test_retries_raises_exception():
    state = {'r': 0, 'h': 0, 'tries': 5}

    def a_hook(tries_remaining, e, delay):
        assert_equal(tries_remaining, state['tries']-state['r'])
        assert_equal(e.message, 'integer division or modulo by zero')
        assert_equal(delay, 0.0)
        state['h'] += 1

    @retries(state['tries'], delay=0,
             exceptions=(ZeroDivisionError,), hook=a_hook)
    def never_works():
        state['r'] += 1
        x = 5/0

    try:
        never_works()
    except ZeroDivisionError:
        pass
    else:
        raise Exception("Failed to Raise ZeroDivisionError")

    assert_equal(state['r'], 5)
    assert_equal(state['h'], 4)
