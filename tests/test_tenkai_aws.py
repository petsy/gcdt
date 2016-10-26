import os

import boto3
from pyhocon import ConfigFactory
from nose.plugins.attrib import attr
from nose.tools import with_setup, assert_equal, assert_false
import pytest

from gcdt.logger import setup_logger
from gcdt.kumo_core import deploy_stack, are_credentials_still_valid, \
    load_cloudformation_template, delete_stack, _get_stack_name
from gcdt.tenkai_core import deploy as tenkai_deploy, deployment_status
from gcdt.utils import get_outputs_for_stack
from .helpers_aws import check_preconditions, cleanup_buckets, boto_session

log = setup_logger(logger_name='tenkai_test_aws')


def here(p): return os.path.join(os.path.dirname(__file__), p)


# read template and config
config_sample_codeploy_stack = ConfigFactory.parse_file(
    here('resources/sample_codedeploy_app/settings_dev.conf')
)


@pytest.fixture(scope='function')  # 'function' or 'module'
def cleanup_stack_tenkai(boto_session):
    """Remove the ec2 stack to cleanup after test run.

    This is intended to be called during test teardown"""
    yield
    # cleanup
    exit_code = delete_stack(boto_session, config_sample_codeploy_stack)
    # check whether delete was completed!
    assert_false(exit_code, 'delete_stack was not completed\n' +
                 'please make sure to clean up the stack manually')


@attr('aws')
@with_setup(check_preconditions, cleanup_stack_tenkai)
def test_tenkai_exit_codes(cleanup_stack_tenkai, boto_session):
    # TDODO: cleanup two tests in one
    are_credentials_still_valid(boto_session)
    # Set up stack with an ec2 and deployment
    cloudformation, _ = load_cloudformation_template(
        here('resources/sample_codedeploy_app/cloudformation.py')
    )
    exit_code = deploy_stack(boto_session, config_sample_codeploy_stack,
                             cloudformation, override_stack_policy=False)
    assert_equal(exit_code, 0)

    stack_name = _get_stack_name(config_sample_codeploy_stack)
    stack_output = get_outputs_for_stack(boto_session, stack_name)
    app_name = stack_output.get('ApplicationName', None)
    deployment_group = stack_output.get('DeploymentGroupName', None)
    cwd = here('.')

    not_working_deploy_dir = here(
        './resources/sample_codedeploy_app/not_working')
    working_deploy_dir = here('./resources/sample_codedeploy_app/working')
    os.chdir(not_working_deploy_dir)

    # test deployment which should exit with exit code 1
    deploy_id_1 = tenkai_deploy(
        boto_session,
        app_name,
        deployment_group,
        'CodeDeployDefault.AllAtOnce',
        '7finity-dp-dev-deployment'
    )

    exit_code = deployment_status(boto_session, deploy_id_1)
    assert_equal(exit_code, 1)
    # test deployment which should exit with exit code 0
    os.chdir(working_deploy_dir)
    deploy_id_2 = tenkai_deploy(
        boto_session,
        app_name,
        deployment_group,
        'CodeDeployDefault.AllAtOnce',
        '7finity-dp-dev-deployment'
    )
    exit_code = deployment_status(boto_session, deploy_id_2)
    assert_equal(exit_code, 0)
    os.chdir(cwd)
