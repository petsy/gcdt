#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The 'tenkai' tool is used to work with AWS CodeDeploy.
"""

from __future__ import print_function
import sys

import botocore
from docopt import docopt

from . import utils
from .tenkai_core import deploy, deployment_status, \
    bundle_revision
from gcdt.s3 import prepare_artifacts_bucket
from .utils import check_gcdt_update
from .monitoring import datadog_error, datadog_event_detail
from .gcdt_cmd_dispatcher import cmd, get_command
from .gcdt_lifecycle import lifecycle
from .gcdt_awsclient import AWSClient

DOC = '''Usage:
        tenkai bundle
        tenkai deploy
        tenkai version

-h --help           show this
'''


@cmd(spec=['version'])
def version_cmd():
    check_gcdt_update()
    utils.version()
    sys.exit(0)


@cmd(spec=['deploy'])
def deploy_cmd(**tooldata):
    context = tooldata.get('context')
    conf = tooldata.get('config')
    awsclient = context.get('awsclient')

    # are_credentials_still_valid()
    prepare_artifacts_bucket(awsclient,
                             conf.get('codedeploy.artifactsBucket'))
    deployment = deploy(
        awsclient=awsclient,
        applicationName=conf.get('codedeploy.applicationName'),
        deploymentGroupName=conf.get('codedeploy.deploymentGroupName'),
        deploymentConfigName=conf.get('codedeploy.deploymentConfigName'),
        bucket=conf.get('codedeploy.artifactsBucket'),
        pre_bundle_scripts=conf.get('preBundle', None),
        slack_token=context.get('slack_token'),
        slack_channel=context.get('slack_channel')
    )
    exit_code = deployment_status(awsclient, deployment)
    if exit_code:
        datadog_error(context)
        sys.exit(1)
    event = 'tenkai bot: deployed deployment group %s ' % \
            conf.get('codedeploy.deploymentGroupName')
    datadog_event_detail(context, event)


@cmd(spec=['bundle'])
def bundle(**tooldata):
    print('created bundle at %s' % bundle_revision())


def main():
    arguments = docopt(DOC, sys.argv[1:])
    command = get_command(arguments)
    if command == 'version':
        # handle commands that do not need a lifecycle
        cmd.dispatch(arguments)
    else:
        awsclient = AWSClient(botocore.session.get_session())
        lifecycle(awsclient, 'tenkai', command, arguments)


if __name__ == '__main__':
    main()
