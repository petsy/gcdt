#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The 'tenkai' tool is used to work with AWS CodeDeploy.
"""

from __future__ import unicode_literals, print_function
import sys

from . import utils
from .tenkai_core import deploy, deployment_status, \
    bundle_revision
from gcdt.s3 import prepare_artifacts_bucket
from .utils import check_gcdt_update
#from .monitoring import datadog_error, datadog_event_detail
from .gcdt_cmd_dispatcher import cmd
from . import gcdt_lifecycle

DOC = '''Usage:
        tenkai bundle
        tenkai deploy
        tenkai version

-h --help           show this
'''


@cmd(spec=['version'])
def version_cmd():
    utils.version()
    return 1


@cmd(spec=['deploy'])
def deploy_cmd(**tooldata):
    context = tooldata.get('context')
    conf = tooldata.get('config')
    awsclient = context.get('_awsclient')

    # are_credentials_still_valid()
    prepare_artifacts_bucket(awsclient,
                             conf.get('codedeploy.artifactsBucket'))
    deployment = deploy(
        awsclient=awsclient,
        applicationName=conf.get('codedeploy.applicationName'),
        deploymentGroupName=conf.get('codedeploy.deploymentGroupName'),
        deploymentConfigName=conf.get('codedeploy.deploymentConfigName'),
        bucket=conf.get('codedeploy.artifactsBucket'),
        pre_bundle_scripts=conf.get('preBundle', None)
    )
    exit_code = deployment_status(awsclient, deployment)
    if exit_code:
        return 1


@cmd(spec=['bundle'])
def bundle(**tooldata):
    print('created bundle at %s' % bundle_revision())


if __name__ == '__main__':
    sys.exit(gcdt_lifecycle.main(DOC, 'tenkai'))
