# -*- coding: utf-8 -*-
import boto3
import os
from StringIO import StringIO
from nose.tools import assert_equal, assert_false, \
    assert_regexp_matches, with_setup
import nose
from nose.tools import assert_is_not
from nose.plugins.attrib import attr
from pyhocon import ConfigFactory
from pyhocon.config_tree import ConfigTree
from gcdt.kumo_core import load_cloudformation_template, list_stacks, \
    print_parameter_diff, are_credentials_still_valid, deploy_stack, \
    delete_stack, create_change_set, _get_stack_name, describe_change_set, \
    _get_artifact_bucket, _s3_upload
from helpers import check_preconditions


def here(p): return os.path.join(os.path.dirname(__file__), p)

# slack_token for testing (the one Jenkins uses):
slack_token = '***REMOVED***'

boto_session = boto3.session.Session()

# read template and config
cloudformation, _ = load_cloudformation_template(
    here('resources/simple_cloudformation_stack/cloudformation.py')
)
config = ConfigFactory.parse_file(
    here('resources/simple_cloudformation_stack/settings_dev.conf')
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
    # expected = ConfigTree([('kumo', ConfigTree([('slack-token', stackname)]))])

    artifact_bucket = _get_artifact_bucket(upload_conf)
    _prepare_artifacts_bucket(artifact_bucket)
    dest_key = 'kumo/%s/%s-cloudformation.json' % (region,
                                                   _get_stack_name(upload_conf))
    expected_s3url = 'https://s3-%s.amazonaws.com/%s/%s' % (region,
                                                            artifact_bucket,
                                                            dest_key)

    actual_s3url = _s3_upload(boto_session, upload_conf, cloudformation)
    assert_equal(expected_s3url, actual_s3url)


# most kumo-operations which rely on a stack on AWS can not be tested in isolation
# since the stack creation for a simple stack takes some time we decided
# to test the stack related operations together

def cleanup_stack():
    """Remove the stack to cleanup after test run.

    This is intended to be called during test teardown"""
    exit_code = delete_stack(boto_session, config, slack_token)
    # check whether delete was completed!
    assert_false(exit_code, 'delete_stack was not completed\n' +
                 'please make sure to clean up the stack manually')


@attr('aws')
@with_setup(check_preconditions, cleanup_stack)
def test_kumo_stack_lifecycle():
    # create a stack we use for the test lifecycle
    print_parameter_diff(boto_session, config)
    are_credentials_still_valid(boto_session)
    exit_code = deploy_stack(boto_session, config, cloudformation,
                             slack_token, override_stack_policy=False)
    assert_equal(exit_code, 0)

    ## preview (with identical stack)
    # TODO: add more asserts!
    change_set_name, stackname = \
        create_change_set(boto_session, config, cloudformation)
    assert_equal(stackname, _get_stack_name(config))
    assert_is_not(change_set_name, '')
    describe_change_set(boto_session, change_set_name, stackname)

    ## update the stack
    print_parameter_diff(boto_session, config)
    exit_code = deploy_stack(boto_session, config, cloudformation,
                             slack_token, override_stack_policy=False)
    assert_equal(exit_code, 0)
