#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The 'kumo' tool is used to deploy infrastructure CloudFormation templates
to AWS cloud.
"""

from __future__ import unicode_literals, print_function
import sys
import json
from tempfile import NamedTemporaryFile

from clint.textui import colored

from . import utils
from .kumo_core import print_parameter_diff, delete_stack, \
    deploy_stack, generate_template_file, list_stacks, create_change_set, \
    describe_change_set, load_cloudformation_template, call_pre_hook
from .utils import read_gcdt_user_config, check_gcdt_update
from .monitoring import datadog_event_detail
from .kumo_viz import cfn_viz, svg_output
from .gcdt_cmd_dispatcher import cmd
from . import gcdt_lifecycle


# creating docopt parameters and usage help
DOC = '''Usage:
        kumo deploy [--override-stack-policy]
        kumo list
        kumo delete -f
        kumo generate
        kumo preview
        kumo version
        kumo dot

-h --help           show this
'''


def load_template():
    """Bail out if template is not found.
    """
    cloudformation, found = load_cloudformation_template()
    if not found:
        print(colored.red('no cloudformation.py found, bailing out...'))
        sys.exit(1)
    return cloudformation


def get_user_config():
    slack_token, slack_channel = read_gcdt_user_config(compatibility_mode='kumo')
    if not slack_token and not isinstance(slack_token, basestring):
        sys.exit(1)
    else:
        return slack_token, slack_channel


@cmd(spec=['version'])
def version_cmd():
    check_gcdt_update()
    utils.version()


@cmd(spec=['dot'])
def dot_cmd(**tooldata):
    #context = tooldata.get('context')
    conf = tooldata.get('config')
    cloudformation = load_template()
    with NamedTemporaryFile(delete=False) as temp_dot:
        cfn_viz(json.loads(cloudformation.generate_template()),
                parameters=conf,
                out=temp_dot)
        temp_dot.close()
        return svg_output(temp_dot.name)


@cmd(spec=['deploy', '--override-stack-policy'])
def deploy_cmd(override, **tooldata):
    context = tooldata.get('context')
    conf = tooldata.get('config')
    awsclient = context.get('awsclient')

    slack_token, slack_channel = get_user_config()
    cloudformation = load_template()
    call_pre_hook(awsclient, cloudformation)
    print_parameter_diff(awsclient, conf)
    exit_code = deploy_stack(awsclient, conf, cloudformation, slack_token, \
                             slack_channel, override_stack_policy=override)
    event = 'kumo bot: deployed stack %s ' % conf.get('cloudformation.StackName')
    datadog_event_detail(context, event)
    return exit_code


@cmd(spec=['delete', '-f'])
def delete_cmd(force, **tooldata):
    context = tooldata.get('context')
    conf = tooldata.get('config')
    awsclient = context.get('awsclient')
    slack_token, slack_channel = get_user_config()
    exit_code = delete_stack(awsclient, conf, slack_token, slack_channel)
    event = 'kumo bot: deleted stack %s ' % conf.get('cloudformation.StackName')
    datadog_event_detail(context, event)
    return exit_code


@cmd(spec=['generate'])
def generate_cmd(**tooldata):
    #context = tooldata.get('context')
    conf = tooldata.get('config')
    cloudformation = load_template()
    generate_template_file(conf, cloudformation)


@cmd(spec=['list'])
def list_cmd(**tooldata):
    context = tooldata.get('context')
    conf = tooldata.get('config')
    awsclient = context.get('awsclient')
    list_stacks(awsclient)


@cmd(spec=['preview'])
def list_cmd(**tooldata):
    context = tooldata.get('context')
    conf = tooldata.get('config')
    awsclient = context.get('awsclient')
    cloudformation = load_template()
    print_parameter_diff(awsclient, conf)
    change_set, stack_name = create_change_set(awsclient, conf,
                                               cloudformation)
    describe_change_set(awsclient, change_set, stack_name)


if __name__ == '__main__':
    sys.exit(gcdt_lifecycle.main(DOC, 'kumo'))
