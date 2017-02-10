# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import os
from tempfile import NamedTemporaryFile

from nose.tools import assert_equal, assert_is_not_none
import pytest

from gcdt import utils
from gcdt.utils import version, __version__, retries, configure, \
    read_gcdt_user_config, get_command, read_gcdt_user_config_value, \
    execute_scripts, dict_merge
from .helpers import create_tempfile, cleanup_tempfiles
from . import here


def test_version(capsys):
    version()
    out, err = capsys.readouterr()
    assert out.strip() == 'gcdt version %s' % __version__


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


def test_configure():
    stackname = 'my_stack'

    def fake_get_input():
        return stackname

    utils._get_slack_token_from_user = fake_get_input

    tf = NamedTemporaryFile(delete=False)
    configure(tf.name)
    assert_equal(open(tf.name).read(), 'gcdt {\nslack-token=%s\n}' % stackname)

    # cleanup the testfile
    tf.close()
    os.unlink(tf.name)


def test_read_user_config():
    expected_slack_token = 'my_slack_token'
    expected_slack_channel = 'my_slack_channel'

    tf = NamedTemporaryFile(delete=False)
    open(tf.name, 'w').write('gcdt {\nslack-token=%s\nslack-channel=%s\n}' %
                             (expected_slack_token, expected_slack_channel))

    slack_token, slack_channel = read_gcdt_user_config(tf.name)
    assert_equal(slack_token, expected_slack_token)
    assert_equal(slack_channel, expected_slack_channel)

    # cleanup the testfile
    tf.close()
    os.unlink(tf.name)


def test_read_user_config_comp_mode():
    expected_slack_token = 'my_slack_token'

    tf = NamedTemporaryFile(delete=False)
    open(tf.name, 'w').write('kumo {\nslack-token=%s\n}' % expected_slack_token)

    slack_token, slack_channel = read_gcdt_user_config(tf.name, 'kumo')
    assert_equal(slack_token, expected_slack_token)
    assert_equal(slack_channel, 'systemmessages')

    # cleanup the testfile
    tf.close()
    os.unlink(tf.name)


def test_read_gcdt_user_config_value(cleanup_tempfiles):
    tf = create_tempfile('ramuda {\nfailDeploymentOnUnsuccessfulPing=true\n}')
    cleanup_tempfiles.append(tf)

    value = read_gcdt_user_config_value(
        'ramuda.failDeploymentOnUnsuccessfulPing', gcdt_file=tf)
    assert value is True


def test_read_gcdt_user_config_value_default(cleanup_tempfiles):
    tf = create_tempfile('ramuda {\nfailDeploymentOnUnsuccessfulPing=true\n}')
    cleanup_tempfiles.append(tf)

    value = read_gcdt_user_config_value('ramuda.thisValueIsNotPresent',
                                        default='my_default', gcdt_file=tf)
    assert value == 'my_default'


def test_command_version():
    arguments = {
        '-f': False,
        'configure': False,
        'delete': False,
        'version': True
    }
    assert_equal(get_command(arguments), 'version')


def test_command_delete_f():
    arguments = {
        '-f': True,
        'configure': False,
        'delete': True,
        'version': False
    }
    assert_equal(get_command(arguments), 'delete')


def test_dict_merge():
    a = {'1': 1, '2': [2], '3': {'3': 3}}
    dict_merge(a, {'3': 3})
    assert a == {'1': 1, '2': [2], '3': 3}

    dict_merge(a, {'4': 4})
    assert a == {'1': 1, '2': [2], '3': 3, '4': 4}

    dict_merge(a, {'4': {'4': 4}})
    assert a == {'1': 1, '2': [2], '3': 3, '4': {'4': 4}}

    dict_merge(a, {'4': {'5': 5}})
    assert a == {'1': 1, '2': [2], '3': 3, '4': {'4': 4, '5': 5}}

    dict_merge(a, {'2': [2, 2], '4': [4]})
    assert a == {'1': 1, '2': [2, 2], '3': 3, '4': [4]}


# TODO get_outputs_for_stack
# TODO test_make_command
