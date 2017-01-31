# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import copy
import inspect
from functools import update_wrapper

from . import gcdt_signals, __version__
from .monitoring import datadog_notification
from .gcdt_defaults import DEFAULT_CONFIG
from .utils import dict_merge, read_gcdt_user_config, get_context
from .config_reader import read_config
from .gcdt_cmd_dispatcher import cmd
from .gcdt_plugins import load_plugins

# lifecycle implementation adapted from
# https://github.com/finklabs/aws-deploy/blob/master/aws_deploy/tool.py


def lifecycle(boto_session, arguments):
    """Tool lifecycle which provides hooks into the different stages of the
    command execution. See signals for hook details.
    """
    # TODO check gcdt update!
    load_plugins()
    # TODO find out tool and command!!!
    tool = 'tenkai'
    command = 'version'
    #click_xtc = click.get_current_context()
    #tool = click_xtc.parent.info_name
    #command = click_xtc.info_name
    ########## context!!!
    context = get_context(boto_session, tool, command)
    # every tool needs a boto_session so we provide this via the context
    # TODO not sure if bote_session needs to go into context!!
    context['boto_session'] = boto_session

    gcdt_signals.initialized.send(context)

    gcdt_signals.config_read_init.send(context)
    #config = read_config(boto_session, config_base_name=DEFAULT_CONFIG[tool].get(
    #    'config_base_name', tool))
    config = {}
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
        cmd.dispatch(arguments, context=context, config=config)
    except Exception as e:
        print('bam')
        print(str(e))
        context['error'] = str(e)
        gcdt_signals.error.send((context, config))
        return

    gcdt_signals.command_finalized.send((context, config))

    # TODO reporting (in case you want to get a summary / output to the user)

    gcdt_signals.finalized.send(context)
