# -*- coding: utf-8 -*-
import pytest

from gcdt.cmd_dispatcher import cmd


'''This is the sample scenario:

Usage:
    sample.py -h
    sample.py cmd1
    sample.py cmd2 [-f|-h]
    sample.py cmd3 <dest>

Options:
    -f --force      Force.
    -h --help       show this
'''

result = {}


@cmd(spec=['cmd1'])
def cmd1():
    result['cmd1'] = result.get('cmd1', 0) + 1


@cmd(spec=['cmd2', '--force'])
def cmd2(force):
    assert force is True
    result['cmd2'] = result.get('cmd2', 0) + 1


@cmd(spec=['cmd2_no_force', '--force'])
def cmd2_no_force(force):
    assert force is False
    result['cmd2'] = result.get('cmd2', 0) + 1


@cmd(spec=['cmd3', '<dest>'])
def cmd3(dest):
    assert dest == 'my_destination'
    result['cmd3'] = result.get('cmd3', 0) + 1


@cmd(spec=['--help'])
def handle_help(help):
    assert help is True
    result['help'] = result.get('help', 0) + 1


# note: we do exact cmd matching so we can exchange position with the previous
# one without changing anything
@cmd(spec=['cmd2', '--help'])
def handle_cmd2_help(help):
    assert help is True
    result['cmd2'] = result.get('cmd2', 0) + 1
    result['help'] = result.get('help', 0) + 1


def test_cmd1_is_called():
    global result
    result = {}

    # note: no parsing of args here!!
    # args = docopt(DOC)
    cmd.dispatch({
        '--force': False,
        '--help': False,
        'cmd1': True,
        'cmd2': False,
        'cmd3': False,
        '<dest>': None}
    )
    assert result == {'cmd1': 1}


def test_cmd2_is_called():
    global result
    result = {}

    cmd.dispatch({
        '--force': True,
        '--help': False,
        'cmd1': False,
        'cmd2': True,
        'cmd3': False,
        '<dest>': None}
    )
    assert result == {'cmd2': 1}


def test_cmd2_with_force_option_false():
    global result
    result = {}

    cmd.dispatch({
        '--force': False,
        '--help': False,
        'cmd1': False,
        'cmd2_no_force': True,
        'cmd3': False,
        '<dest>': None}
    )
    assert result == {'cmd2': 1}


def test_cmd3_is_called():
    global result
    result = {}

    cmd.dispatch({
        '--force': False,
        '--help': False,
        'cmd1': False,
        'cmd2': False,
        'cmd3': True,
        '<dest>': 'my_destination'}
    )
    assert result == {'cmd3': 1}


def test_help():
    global result
    result = {}

    cmd.dispatch({
        '--force': False,
        '--help': True,
        'cmd1': False,
        'cmd2': False,
        'cmd3': False,
        '<dest>': None}
    )
    assert result == {'help': 1}


def test_cmd2_help():
    global result
    result = {}

    cmd.dispatch({
        '--force': False,
        '--help': True,
        'cmd1': False,
        'cmd2': True,
        'cmd3': False,
        '<dest>': None}
    )
    assert result == {'help': 1, 'cmd2': 1}


def test_cmd_exception_when_not_spec_does_not_match():
    global result
    result = {}

    with pytest.raises(Exception) as einfo:
        cmd.dispatch({
            '--force': False,
            '--help': False,
            'cmd1': False,
            'cmd2': False,
            'cmd3': True}
        )
    assert result == {}
    assert einfo.match(r'No implementation for spec: .*')


def test_cmd_exception_on_missing_option():
    global result
    result = {}

    with pytest.raises(Exception) as einfo:
        cmd.dispatch({
            '--force': True,
            '--help': False,
            'cmd1': False,
            'cmd2': False,
            'cmd3': True,
            '<dest>': None}
        )
    assert result == {}
    assert einfo.match(r'No implementation for spec: .*')
