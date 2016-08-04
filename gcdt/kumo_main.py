#!/usr/bin/env python

"""The 'kumo' tool is used to deploy infrastructure CloudFormation templates
to AWS cloud.
"""

from __future__ import print_function

import sys
import utils
import boto3
from docopt import docopt
from clint.textui import colored
from glomex_utils.config_reader import read_config
from kumo_core import call_pre_hook, print_parameter_diff, delete_stack, \
    deploy_stack, generate_template_file, list_stacks, configure, \
    create_change_set, describe_change_set, \
    load_cloudformation_template


# creating docopt parameters and usage help
doc = """Usage:
        kumo deploy [--override-stack-policy]
        kumo list
        kumo delete -f
        kumo generate
        kumo configure
        kumo preview
        kumo version

-h --help           show this

"""


def load_template():
    """Bail out if template is not found.
    """
    cloudformation, found = load_cloudformation_template()
    if not found:
        print(colored.red('no cloudformation.py found, bailing out...'))
        sys.exit(1)
    return cloudformation


def are_credentials_still_valid(boto_session):
    """Wrapper to bail out on invalid credentials."""
    from kumo_core import are_credentials_still_valid as acsv
    exit_code = acsv(boto_session)
    if exit_code:
        sys.exit(1)


def read_kumo_config():
    """Wrapper to bail out on invalid credentials."""
    from kumo_core import read_kumo_config as rkc
    kumo_config, exit_code = rkc()
    if exit_code:
        sys.exit(1)
    else:
        return kumo_config


def get_slack_token():
    KUMO_CONFIG = read_kumo_config()
    slack_token = KUMO_CONFIG.get('kumo.slack-token')
    return slack_token


def main():
    exit_code = 0
    boto_session = boto3.session.Session()
    arguments = docopt(doc)

    # Run command
    if arguments['deploy']:
        slack_token = get_slack_token()
        cloudformation = load_template()
        call_pre_hook(cloudformation)
        conf = read_config()
        print_parameter_diff(boto_session, conf)
        are_credentials_still_valid(boto_session)
        exit_code = deploy_stack(boto_session, conf, cloudformation, slack_token,
                     override_stack_policy=arguments['--override-stack-policy'])
    elif arguments['delete']:
        slack_token = get_slack_token()
        cloudformation = load_template()  # TODO: is this really necessary?
        conf = read_config()
        are_credentials_still_valid(boto_session)
        exit_code = delete_stack(boto_session, conf, slack_token)
    elif arguments['generate']:
        cloudformation = load_template()
        conf = read_config()
        generate_template_file(conf, cloudformation)
    elif arguments['list']:
        are_credentials_still_valid(boto_session)
        list_stacks(boto_session)
    elif arguments['configure']:
        configure()
    elif arguments['preview']:
        cloudformation = load_template()
        conf = read_config()
        print_parameter_diff(boto_session, conf)
        are_credentials_still_valid(boto_session)
        change_set, stack_name = create_change_set(boto_session, conf,
                                                   cloudformation)
        describe_change_set(change_set, stack_name)
    elif arguments['version']:
        utils.version()

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
