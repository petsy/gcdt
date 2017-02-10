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


@cmd(spec=['version'])
def version_cmd():
    utils.version()


@cmd(spec=['dot'])
def dot_cmd(**tooldata):
    #context = tooldata.get('context')
    conf = tooldata.get('config')
    cloudformation = load_template()
    with NamedTemporaryFile() as temp_dot:
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

    cloudformation = load_template()
    call_pre_hook(awsclient, cloudformation)
    print_parameter_diff(awsclient, conf)
    exit_code = deploy_stack(awsclient, conf, cloudformation,
                             override_stack_policy=override)
    event = 'kumo bot: deployed stack %s ' % conf.get('cloudformation.StackName')
    datadog_event_detail(context, event)
    return exit_code


@cmd(spec=['delete', '-f'])
def delete_cmd(force, **tooldata):
    context = tooldata.get('context')
    conf = tooldata.get('config')
    awsclient = context.get('awsclient')
    exit_code = delete_stack(awsclient, conf)
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
    #conf = tooldata.get('config')
    awsclient = context.get('awsclient')
    list_stacks(awsclient)


@cmd(spec=['preview'])
def preview_cmd(**tooldata):
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
