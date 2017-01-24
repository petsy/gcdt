#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The 'tenkai' tool is used to work with AWS CodeDeploy.
"""

from __future__ import print_function
import sys

import boto3
from docopt import docopt

from .config_reader import read_config
from gcdt import utils
from gcdt.tenkai_core import prepare_artifacts_bucket, deploy, deployment_status, \
    bundle_revision
from gcdt.utils import get_context, get_command, read_gcdt_user_config
from gcdt.monitoring import datadog_notification, datadog_error, datadog_event_detail


DOC = '''Usage:
        tenkai bundle
        tenkai deploy
        tenkai version

-h --help           show this
'''


def get_user_config():
    slack_token, slack_channel = read_gcdt_user_config(compatibility_mode='tenkai')
    if not slack_token and not isinstance(slack_token, basestring):
        sys.exit(1)
    else:
        return slack_token, slack_channel


def main():
    arguments = docopt(DOC)
    if arguments['version']:
        utils.version()
        sys.exit(0)

    boto_session = boto3.session.Session()
    context = get_context('tenkai', get_command(arguments))
    datadog_notification(context)

    if arguments['deploy']:
        slack_token, slack_channel = get_user_config()
        conf = read_config(config_base_name='codedeploy')

        # are_credentials_still_valid()
        prepare_artifacts_bucket(boto_session,
                                 conf.get('codedeploy.artifactsBucket'))
        deployment = deploy(
            boto_session=boto_session,
            applicationName=conf.get('codedeploy.applicationName'),
            deploymentGroupName=conf.get('codedeploy.deploymentGroupName'),
            deploymentConfigName=conf.get('codedeploy.deploymentConfigName'),
            bucket=conf.get('codedeploy.artifactsBucket'),
            pre_bundle_scripts=conf.get('preBundle', None),
            slack_token=slack_token,
            slack_channel=slack_channel
        )
        exit_code = deployment_status(boto_session, deployment)
        if exit_code:
            datadog_error(context)
            sys.exit(1)
        event = 'tenkai bot: deployed deployment group %s ' % \
                  conf.get('codedeploy.deploymentGroupName')
        datadog_event_detail(context, event)
    elif arguments['bundle']:
        print('created bundle at %s' % bundle_revision())


if __name__ == '__main__':
    main()
