# -*- coding: utf-8 -*-
import boto3
import os
from StringIO import StringIO
from nose.tools import assert_equal, assert_false, \
    assert_regexp_matches, assert_is_not_none, with_setup
import nose
from nose.tools import assert_is_not, assert_true
from nose.plugins.attrib import attr
from pyhocon import ConfigFactory
from pyhocon.config_tree import ConfigTree
from gcdt.kumo_core import load_cloudformation_template, list_stacks, \
    print_parameter_diff, are_credentials_still_valid, deploy_stack, \
    delete_stack, create_change_set, _get_stack_name, describe_change_set, \
    _get_artifact_bucket, _s3_upload
from gcdt.kumo_util import ensure_ebs_volume_tags_ec2_instance, ensure_ebs_volume_tags_autoscaling_group
from glomex_utils.servicediscovery import get_outputs_for_stack
from helpers import check_preconditions


def here(p): return os.path.join(os.path.dirname(__file__), p)

boto_session = boto3.session.Session()

# read template and config
config_simple_stack = ConfigFactory.parse_file(
    here('resources/simple_cloudformation_stack/settings_dev.conf')
)

config_ec2 = ConfigFactory.parse_file(
    here('resources/sample_ec2_cloudformation_stack/settings_dev.conf')
)

config_autoscaling = ConfigFactory.parse_file(
    here('resources/sample_autoscaling_cloudformation_stack/settings_dev.conf')
)

@attr('aws')
@with_setup(check_preconditions)
def test_list_stacks():
    out = StringIO()
    list_stacks(boto_session, out=out)
    assert_regexp_matches(out.getvalue().strip(), 'listed \d+ stacks')


@attr('aws')
@with_setup(check_preconditions)
def test_print_parameter_diff():
    out = StringIO()
    empty_conf = ConfigTree([('cloudfoundation', ConfigTree([]))])

    print_parameter_diff(boto_session, empty_conf, out=out)
    assert_regexp_matches(out.getvalue().strip(),
        'StackName is not configured, could not create parameter diff')


# TODO: this needs a cleanup of the bucket
@attr('aws')
@with_setup(check_preconditions)
def test_s3_upload():
    # bucket helpers borrowed from tenkai
    def _prepare_artifacts_bucket(bucket):
        if not _bucket_exists(bucket):
            _create_bucket(bucket)

    def _bucket_exists(bucket):
        s3 = boto_session.resource('s3')
        return s3.Bucket(bucket) in s3.buckets.all()

    def _create_bucket(bucket):
        client = boto_session.client('s3')
        client.create_bucket(
            Bucket=bucket
        )
        client.put_bucket_versioning(
            Bucket=bucket,
            VersioningConfiguration={
                'Status': 'Enabled'
            }
        )

    upload_conf = ConfigFactory.parse_file(
        here('resources/simple_cloudformation_stack/settings_upload_dev.conf')
    )

    region = boto_session.region_name
    account = os.getenv('ACCOUNT', None)
    # add account prefix to artifact bucket config
    if account:
        upload_conf['cloudformation']['artifactBucket'] = \
            '%s-unittest-kumo-artifact-bucket' % account

    artifact_bucket = _get_artifact_bucket(upload_conf)
    _prepare_artifacts_bucket(artifact_bucket)
    dest_key = 'kumo/%s/%s-cloudformation.json' % (region,
                                                   _get_stack_name(upload_conf))
    expected_s3url = 'https://s3-%s.amazonaws.com/%s/%s' % (region,
                                                            artifact_bucket,
                                                            dest_key)
    cloudformation_simple_stack, _ = load_cloudformation_template(
        here('resources/simple_cloudformation_stack/cloudformation.py')
    )
    actual_s3url = _s3_upload(boto_session, upload_conf, cloudformation_simple_stack)
    assert_equal(expected_s3url, actual_s3url)


# most kumo-operations which rely on a stack on AWS can not be tested in isolation
# since the stack creation for a simple stack takes some time we decided
# to test the stack related operations together

def cleanup_stack():
    """Remove the stack to cleanup after test run.

    This is intended to be called during test teardown"""
    exit_code = delete_stack(boto_session, config_simple_stack)
    # check whether delete was completed!
    assert_false(exit_code, 'delete_stack was not completed\n' +
                 'please make sure to clean up the stack manually')

def cleanup_stack_autoscaling():
    """Remove the autoscaling stack to cleanup after test run.

    This is intended to be called during test teardown"""
    exit_code = delete_stack(boto_session, config_autoscaling)
    # check whether delete was completed!
    assert_false(exit_code, 'delete_stack was not completed\n' +
                 'please make sure to clean up the stack manually')

def cleanup_stack_ec2():
    """Remove the ec2 stack to cleanup after test run.

    This is intended to be called during test teardown"""
    exit_code = delete_stack(boto_session, config_ec2)
    # check whether delete was completed!
    assert_false(exit_code, 'delete_stack was not completed\n' +
                 'please make sure to clean up the stack manually')


@attr('aws')
@with_setup(check_preconditions, cleanup_stack)
def test_kumo_stack_lifecycle():
    # create a stack we use for the test lifecycle


    print_parameter_diff(boto_session, config_simple_stack)
    are_credentials_still_valid(boto_session)
    cloudformation_simple_stack, _ = load_cloudformation_template(
        here('resources/simple_cloudformation_stack/cloudformation.py')
    )
    exit_code = deploy_stack(boto_session, config_simple_stack, cloudformation_simple_stack,
                             override_stack_policy=False)
    assert_equal(exit_code, 0)

    ## preview (with identical stack)
    # TODO: add more asserts!
    change_set_name, stackname = \
        create_change_set(boto_session, config_simple_stack, cloudformation_simple_stack)
    assert_equal(stackname, _get_stack_name(config_simple_stack))
    assert_is_not(change_set_name, '')
    describe_change_set(boto_session, change_set_name, stackname)

    ## update the stack
    print_parameter_diff(boto_session, config_simple_stack)
    exit_code = deploy_stack(boto_session, config_simple_stack, cloudformation_simple_stack,
                             override_stack_policy=False)
    assert_equal(exit_code, 0)


@attr('aws')
@with_setup(check_preconditions, cleanup_stack_autoscaling)
def test_kumo_utils_ensure_autoscaling_ebs_tags():
    are_credentials_still_valid(boto_session)
    cloudformation_autoscaling, _ = load_cloudformation_template(
        here('resources/sample_autoscaling_cloudformation_stack/cloudformation.py')
    )

    exit_code = deploy_stack(boto_session, config_autoscaling, cloudformation_autoscaling,
                             override_stack_policy=False)
    assert_equal(exit_code, 0)
    stack_name = _get_stack_name(config_autoscaling)
    stack_output = get_outputs_for_stack(stack_name)
    as_group_name = stack_output.get('AutoScalingGroupName', None)
    assert_is_not_none(as_group_name)
    tag_v1 = {
        'Key':'kumo-test',
        'Value':'version1'
    }
    tags_v1 = [
        tag_v1
    ]
    ensure_ebs_volume_tags_autoscaling_group(as_group_name, tags_v1)

    autoscale_filter = {
        'Name':'tag:aws:autoscaling:groupName',
        'Values': [ as_group_name ]
    }
    ec2_client = boto3.client('ec2')
    ec2_resource = boto3.resource('ec2')
    response = ec2_client.describe_instances( Filters = [ autoscale_filter ])
    for r in response['Reservations']:
        for i in r['Instances']:
            instance_id = i['InstanceId']
            instance  = ec2_resource.Instance(instance_id)
            for vol in instance.volumes.all():
                for tag in tags_v1:
                    assert_true(assert_volume_tagged(vol, tag))

    tag_v2 = {
        'Key':'kumo-test',
        'Value':'version2'
    }
    tags_v2  = [
        tag_v2
    ]
    ensure_ebs_volume_tags_autoscaling_group(as_group_name, tags_v2)
    for r in response['Reservations']:
        for i in r['Instances']:
            instance_id = i['InstanceId']
            instance  = ec2_resource.Instance(instance_id)
            for vol in instance.volumes.all():
                for tag in tags_v2:
                    assert_true(assert_volume_tagged(vol, tag))
                for tag in tags_v1:
                    assert_false(assert_volume_tagged(vol, tag))



@attr('aws')
@with_setup(check_preconditions, cleanup_stack_ec2)
def test_kumo_utils_ensure_ebs_tags():

    are_credentials_still_valid(boto_session)
    cloudformation_ec2, _ = load_cloudformation_template(
        here('resources/sample_ec2_cloudformation_stack/cloudformation.py')
    )
    exit_code = deploy_stack(boto_session, config_ec2, cloudformation_ec2,
                             override_stack_policy=False)
    assert_equal(exit_code, 0)

    stack_name = _get_stack_name(config_ec2)
    stack_output = get_outputs_for_stack(stack_name)
    instance_id = stack_output.get('InstanceId', None)
    assert_is_not_none(instance_id)
    tag = {
        'Key':'kumo-test',
        'Value':'Success'
    }
    tags = [
        tag
    ]
    ensure_ebs_volume_tags_ec2_instance(instance_id, tags)
    ec2_resource = boto3.resource('ec2')
    instance  = ec2_resource.Instance(instance_id)
    for vol in instance.volumes.all():
        for tag in tags:
            assert_true(assert_volume_tagged(vol, tag))

def assert_volume_tagged(vol, tag):
    if vol.tags:
        if tag in vol.tags:
            return True
        else:
            return False
    else:
        return False


