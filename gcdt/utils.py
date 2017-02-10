# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

import getpass
import subprocess
import sys
from time import sleep

import os
from clint.textui import prompt, colored
from pyhocon import ConfigFactory

from gcdt import __version__
from gcdt.config_reader import _get_datadog_api_key
from gcdt.package_utils import get_package_versions


#def version(out=sys.stdout):
#    """Print version of gcdt tools."""
#    print("gcdt version %s" % __version__, file=out)


def version():
    """Print version of gcdt tools."""
    print("gcdt version %s" % __version__)


def retries(max_tries, delay=1, backoff=2, exceptions=(Exception,), hook=None):
    """Function decorator implementing retrying logic.

    delay: Sleep this many seconds * backoff * try number after failure
    backoff: Multiply delay by this factor after each failure
    exceptions: A tuple of exception classes; default (Exception,)
    hook: A function with the signature:
        example: myhook(tries_remaining, exception, mydelay);
        default: None

    def example_hook(tries_remaining, exception, delay):
        '''Example exception handler; prints a warning to stderr.

        tries_remaining: The number of tries remaining.
        exception: The exception instance which was raised.
        '''
        print >> sys.stderr, "Caught '%s', %d tries remaining, sleeping for %s seconds" % (exception, tries_remaining, delay)

    The decorator will call the function up to max_tries times if it raises
    an exception.

    By default it catches instances of the Exception class and subclasses.
    This will recover after all but the most fatal errors. You may specify a
    custom tuple of exception classes with the 'exceptions' argument; the
    function will only be retried if it raises one of the specified
    exceptions.

    Additionally you may specify a hook function which will be called prior
    to retrying with the number of remaining tries and the exception instance;
    see given example. This is primarily intended to give the opportunity to
    log the failure. Hook is not called after failure if no retries remain.
    """
    def dec(func):
        def f2(*args, **kwargs):
            mydelay = delay
            tries = range(max_tries)
            tries.reverse()
            for tries_remaining in tries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if tries_remaining > 0:
                        if hook is not None:
                            hook(tries_remaining, e, mydelay)
                        sleep(mydelay)
                        mydelay *= backoff
                    else:
                        raise
        return f2
    return dec


# config

def read_gcdt_user_config(gcdt_file=None, compatibility_mode=None):
    """Read .gcdt config file from user home.
    supports compatibility for .kumo, .tenkai, .ramuda, etc. files

    :return: slack_token or None
    """
    extension = 'gcdt'
    if compatibility_mode and compatibility_mode not in \
            ['kumo', 'tenkai', 'ramuda', 'yugen']:
        print(colored.red('Unknown compatibility mode: %s' % compatibility_mode))
        print(colored.red('No user configuration!'))
        return
    elif gcdt_file and compatibility_mode:
        extension = compatibility_mode
    elif not gcdt_file:
        gcdt_file = os.path.expanduser('~') + '/.' + extension
        if os.path.isfile(gcdt_file):
            pass
        elif compatibility_mode:
            extension = compatibility_mode
            gcdt_file = os.path.expanduser('~') + '/.' + extension
    try:
        config = ConfigFactory.parse_file(gcdt_file)
        slack_token = config.get('%s.slack-token' % extension)
        try:
            slack_channel = config.get('%s.slack-channel' % extension)
        except Exception:
            slack_channel = 'systemmessages'
        return slack_token, slack_channel
    except Exception:
        print(colored.red('Cannot find config file .gcdt in your home directory'))
        print(colored.red('Please run \'gcdt configure\''))
        return None, None


def read_gcdt_user_config_value(key, default=None, gcdt_file=None):
    """Read .gcdt config file from user home and return value for key.
    Configuration keys are in the form <command>.<key>

    :return: value if present, or default
    """
    extension = 'gcdt'
    if not gcdt_file:
        gcdt_file = os.path.expanduser('~') + '/.' + extension
    try:
        config = ConfigFactory.parse_file(gcdt_file)
        value = config.get(key)
    except Exception:
        value = default
    return value


def _get_slack_token_from_user():
    slack_token = prompt.query('Please enter your Slack API token: ')
    return slack_token


def configure(config_file=None):
    """Create the .gcdt config file in the users home folder.

    :param config_file:
    """
    if not config_file:
        config_file = os.path.expanduser('~') + '/' + '.gcdt'
    slack_token = _get_slack_token_from_user()
    with open(config_file, 'w') as config:
        config.write('gcdt {\n')
        config.write('slack-token=%s' % slack_token)
        config.write('\n}')


def _get_user():
    return getpass.getuser()


def _get_env():
    """
    Read environment from ENV and mangle it to a (lower case) representation
    :return: Environment as lower case string (or None if not matched)
    """
    env = os.getenv('ENV', os.getenv('env', None))
    if env:
        env = env.lower()
    return env


def get_context(awsclient, tool, command):
    """This assembles the tool context. Private members are preceded by a '_'.

    :param tool:
    :param command:
    :return: dictionary containing the gcdt tool context
    """
    # TODO: elapsed, artifact(stack, depl-grp, lambda, api)
    context = {
        'tool': tool,
        'command': command,
        'version': __version__,
        'user': _get_user()
    }

    env = _get_env()
    if env:
        context['env'] = env

    datadog_api_key = _get_datadog_api_key(awsclient)
    if datadog_api_key:
        context['_datadog_api_key'] = datadog_api_key

    return context


def get_command(arguments):
    """Extract the first argument from arguments parsed by docopt.

    :param arguments parsed by docopt:
    :return: command
    """
    return [k for k, v in arguments.iteritems()
            if not k.startswith('-') and v is True][0]


def execute_scripts(scripts):
    for script in scripts:
        exit_code = _execute_script(script)
        if exit_code != 0:
            return exit_code
    return 0


def _execute_script(file_name):
    if os.path.isfile(file_name):
        print('Executing %s ...' % file_name)
        exit_code = subprocess.call([file_name, '-e'])
        return exit_code
    else:
        print('No file found matching %s...' % file_name)
        return 1


def check_gcdt_update():
    """Check whether a newer gcdt is available and output a warning.

    """
    inst_version, latest_version = get_package_versions('gcdt')
    if inst_version < latest_version:
        print(colored.yellow('Please consider an update to gcdt version: %s' %
                             latest_version))


# adapted from:
# http://stackoverflow.com/questions/7204805/dictionaries-of-dictionaries-merge/7205107#7205107
def dict_merge(a, b, path=None):
    """merges b into a"""
    if path is None:
        path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                dict_merge(a[key], b[key], path + [str(key)])
            elif a[key] != b[key]:
                # update the value
                a[key] = b[key]
        else:
            a[key] = b[key]
    return a
