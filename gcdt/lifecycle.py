# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import os
import copy
import inspect
from functools import update_wrapper

import boto3

from . import signals
from .monitoring import datadog_notification
from .defaults import DEFAULT_CONFIG
from .utils import dict_merge


# lifecycle implementation adapted from
# https://github.com/finklabs/aws-deploy/blob/master/aws_deploy/tool.py

# add fixture feature to pocoo-click
def _make_command(f, name, attrs, cls):
    if isinstance(f, click.Command):
        raise TypeError('Attempted to convert a callback into a '
                        'command twice.')
    new_func = f
    if 'fixture' in attrs:
        fixture = attrs['fixture']
        if not inspect.isgeneratorfunction(fixture):
            raise TypeError('fixture does not yield anything.')
        attrs.pop('fixture')

        def new_func(*args, **kwargs):
            it = fixture()
            val = next(it)
            res = f(val, *args[1:], **kwargs)
            try:
                next(it)
            except StopIteration:
                pass
            else:
                raise RuntimeError('fixture has more than one yield.')
            return res

        try:
            new_func.__click_params__ = f.__click_params__
        except AttributeError:
            pass
        update_wrapper(new_func, f)

    try:
        params = new_func.__click_params__
        params.reverse()
        del new_func.__click_params__
    except AttributeError:
        params = []
    help = attrs.get('help')
    if help is None:
        help = inspect.getdoc(f)
        if isinstance(help, bytes):
            help = help.decode('utf-8')
    else:
        help = inspect.cleandoc(help)
    attrs['help'] = help
    click.decorators._check_for_unicode_literals()
    return cls(name=name or new_func.__name__.lower(),
               callback=new_func, params=params, **attrs)

# patch in the custom command maker
click.decorators._make_command = _make_command


def _get_env():
    """Read ENV environment variable.
    """
    env = os.getenv('ENV', '')
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

    # everybody needs slack, right?
    context['slack_token'], context['slack_channel'] = read_gcdt_user_config()

    env = _get_env()
    if env:
        context['env'] = env

    datadog_api_key = _get_datadog_api_key()
    if datadog_api_key:
        context['_datadog_api_key'] = datadog_api_key

    return context


def lifecycle():
    """Tool lifecycle which provides hooks into the different stages of the
    command execution. See signals for hook details.
    """
    click_xtc = click.get_current_context()
    tool = click_xtc.parent.info_name
    command = click_xtc.info_name
    context = get_context(tool, command)

    signals.initialized.send(context)

    signals.config_read_init.send(context)
    config = read_config(config_base_name=DEFAULT_CONFIG[tool].get(
        'config_base_name', tool))
    signals.config_read_finalized.send(context)

    # every tool needs a boto_session so we provide this via the context
    context['boto_session'] = boto3.session.Session()

    # TODO credentials_retr (in case this would be useful)

    # TODO check credentials are valid

    signals.config_validation_init.send((context, config))
    # TODO config validation
    signals.config_validation_finalized.send((context, config))

    # merge DEFAULT_CONFIG with config
    tool_config = copy.deepcopy(DEFAULT_CONFIG[tool])
    dict_merge(tool_config, config)

    # TODO lookups (in case this would be useful)

    # every tool needs the datadog notifications
    datadog_notification(context)

    # run the command and provide context and config (= tooldata)
    signals.command_init.send((context, config))
    yield context, config
    signals.command_finalized.send((context, config))

    # TODO reporting (in case you want to get a summary / output to the user)

    signals.finalized.send(context)
