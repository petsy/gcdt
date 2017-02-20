#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The 'tenkai' tool is used to work with AWS CodeDeploy.
"""

from __future__ import unicode_literals, print_function
import sys

from . import utils
from .tenkai_core import deploy, deployment_status, bundle_revision
from gcdt.s3 import prepare_artifacts_bucket
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
    config = tooldata.get('config')
    awsclient = context.get('_awsclient')

    prepare_artifacts_bucket(awsclient,
                             #conf.get('codedeploy.artifactsBucket'))
                             config['codedeploy'].get('artifactsBucket'))
    # TODO deprecate prebundle hook with reference to new signal-based-hooks
    pre_bundle_scripts = config.get('preBundle', None)
    if pre_bundle_scripts:
        exit_code = utils.execute_scripts(pre_bundle_scripts)
        if exit_code != 0:
            print('Pre bundle script exited with error')
            return 1

    deployment = deploy(
        awsclient=awsclient,
        #applicationName=conf.get('codedeploy.applicationName'),
        #deploymentGroupName=conf.get('codedeploy.deploymentGroupName'),
        #deploymentConfigName=conf.get('codedeploy.deploymentConfigName'),
        #bucket=conf.get('codedeploy.artifactsBucket')
        applicationName=config['codedeploy'].get('applicationName'),
        deploymentGroupName=config['codedeploy'].get('deploymentGroupName'),
        deploymentConfigName=config['codedeploy'].get('deploymentConfigName'),
        bucket=config['codedeploy'].get('artifactsBucket')
    )

    exit_code = deployment_status(awsclient, deployment)
    if exit_code:
        return 1


@cmd(spec=['bundle'])
def bundle_cmd(**tooldata):
    print('created bundle at %s' % bundle_revision())


def main():
    # TODO: register bundle with bundle signals
    sys.exit(
        gcdt_lifecycle.main(DOC, 'tenkai',
                            dispatch_only=['version', 'bundle'])
    )


if __name__ == '__main__':
    main()
