# -*- coding: utf-8 -*-
from __future__ import print_function

import getpass
import os
import sys
from time import sleep

from clint.textui import prompt, colored
from pyhocon import ConfigFactory
import credstash
from gcdt import __version__


def version(out=sys.stdout):
    """Print version of gcdt tools."""
    print("gcdt version %s" % __version__, file=out)


def get_git_revision_short_hash():
    # TODO: is this a good idea? (how to make sure that git is installed)?
    from string import strip
    import subprocess
    return strip(subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']))


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


def _get_datadog_api_key():
    api_key = None
    try:
        api_key = credstash.getSecret('datadog.api_key')
    except Exception:
        pass
    return api_key


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


def get_context(tool, command):
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

    datadog_api_key = _get_datadog_api_key()
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
