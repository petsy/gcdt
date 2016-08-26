# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import sys
from time import sleep

from clint.textui import prompt, colored
from pyhocon import ConfigFactory
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
                        mydelay = mydelay * backoff
                    else:
                        raise
                else:
                    # break out of the retry loop in success case
                    break
        return f2
    return dec


# config
# TODO: consolidate with other tools!


def read_gcdt_user_config(gcdt_file=None, compatibility_mode=None):
    """Read .gcdt config file from user home.
    supports compatibility for .kumo, .tenkai, .ramuda, etc. files

    :return: slack_token or None
    """
    if not gcdt_file:
        gcdt_file = os.path.expanduser('~') + '/' + '.gcdt'
        try:
            if not os.path.isfile(gcdt_file) \
                    and compatibility_mode in ['kumo', 'tenkai', 'ramuda', 'yugen']:
                # read compatibility_mode file
                comp_mode_file = os.path.expanduser('~') + '/.' + compatibility_mode
                config = ConfigFactory.parse_file(comp_mode_file)
                return config.get('%s.slack-token' % compatibility_mode)
            else:
                # read .gcdt file
                config = ConfigFactory.parse_file(gcdt_file)
                return config.get('gcdt.slack-token')
        except Exception:
            print(colored.red('Cannot find file .gcdt in your home directory'))
            print(colored.red('Please run \'gcdt configure\''))
            return None


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
