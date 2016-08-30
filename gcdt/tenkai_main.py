#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The 'tenkai' tool is used to work with AWS CodeDeploy.
"""

from __future__ import print_function

import sys
from docopt import docopt
from glomex_utils.config_reader import read_config
from gcdt import utils
from gcdt.tenkai_core import prepare_artifacts_bucket, deploy, deployment_status, \
    bundle_revision
from gcdt.utils import get_context, get_command
from gcdt.monitoring import datadog_notification, datadog_error


DOC = '''Usage:
        tenkai bundle
        tenkai deploy
        tenkai version

-h --help           show this
'''


def main():
    arguments = docopt(DOC)
    if arguments['version']:
        utils.version()
        sys.exit(0)

    context = get_context('tenkai', get_command(arguments))
    datadog_notification(context)

    if arguments['deploy']:
        conf = read_config(config_base_name='codedeploy')

        # are_credentials_still_valid()
        prepare_artifacts_bucket(conf.get('codedeploy.artifactsBucket'))
        deployment = deploy(
            applicationName=conf.get('codedeploy.applicationName'),
            deploymentGroupName=conf.get('codedeploy.deploymentGroupName'),
            deploymentConfigName=conf.get('codedeploy.deploymentConfigName'),
            bucket=conf.get('codedeploy.artifactsBucket')
        )
        exit_code = deployment_status(deployment)
        if exit_code:
            datadog_error(context)
            sys.exit(1)
    elif arguments['bundle']:
        print('created bundle at %s' % bundle_revision())


if __name__ == '__main__':
    main()
