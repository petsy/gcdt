# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import copy
import sys

from docopt import docopt
import botocore.session

from . import gcdt_signals
from .monitoring import datadog_notification, datadog_error
from .gcdt_defaults import DEFAULT_CONFIG
from .utils import dict_merge, read_gcdt_user_config, get_context, \
    check_gcdt_update
from .config_reader import read_config
from .gcdt_cmd_dispatcher import cmd, get_command
from .gcdt_plugins import load_plugins
from .gcdt_awsclient import AWSClient


# lifecycle implementation adapted from
# https://github.com/finklabs/aws-deploy/blob/master/aws_deploy/tool.py
def lifecycle(awsclient, tool, command, arguments):
    """Tool lifecycle which provides hooks into the different stages of the
    command execution. See signals for hook details.
    """
    # TODO hooks!!
    load_plugins()
    context = get_context(awsclient, tool, command)
    # every tool needs a awsclient so we provide this via the context
    # TODO not sure if awsclient needs to go into context!!
    context['awsclient'] = awsclient
    context['slack_token'], context['slack_channel'] = \
        read_gcdt_user_config(compatibility_mode='tenkai')

    ## initialized
    gcdt_signals.initialized.send(context)
    check_gcdt_update()

    gcdt_signals.config_read_init.send(context)
    #conf = read_config(awsclient, config_base_name='codedeploy')
    # TODO use awsclient in read_config?
    config = read_config(awsclient._session, config_base_name=
        DEFAULT_CONFIG[tool].get('config_base_name', tool))
    gcdt_signals.config_read_finalized.send(context)

    # TODO credentials_retr (in case this would be useful)

    # TODO check credentials are valid

    gcdt_signals.config_validation_init.send((context, config))
    # TODO config validation
    gcdt_signals.config_validation_finalized.send((context, config))

    # merge DEFAULT_CONFIG with config
    tool_config = copy.deepcopy(DEFAULT_CONFIG[tool])
    dict_merge(tool_config, config)

    # TODO lookups (in case this would be useful)

    # every tool needs the datadog notifications
    # TODO move the datadog notification to plugin!
    datadog_notification(context)

    # run the command and provide context and config (= tooldata)
    gcdt_signals.command_init.send((context, config))
    try:
        exit_code = cmd.dispatch(arguments, context=context, config=config)
    except Exception as e:
        print(str(e))
        context['error'] = str(e)
        gcdt_signals.error.send((context, config))
        exit_code = 1
    if exit_code:
        datadog_error(context)
        return 1

    gcdt_signals.command_finalized.send((context, config))

    # TODO reporting (in case you want to get a summary / output to the user)

    gcdt_signals.finalized.send(context)
    return 0


def main(doc, tool, dispatch_only=None):
    """gcdt tools parametrized main function to initiate gcdt lifecycle.

    :param doc: docopt string
    :param tool: gcdt tool (gcdt, kumo, tenkai, ramuda, yugen)
    :return: exit code
    """
    if dispatch_only is None:
        dispatch_only = ['version']
    assert tool in ['gcdt', 'kumo', 'tenkai', 'ramuda', 'yugen']
    arguments = docopt(doc, sys.argv[1:])
    command = get_command(arguments)
    if command in dispatch_only:
        # handle commands that do not need a lifecycle
        check_gcdt_update()
        return cmd.dispatch(arguments)
    else:
        awsclient = AWSClient(botocore.session.get_session())
        return lifecycle(awsclient, tool, command, arguments)
