# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

import pytest

from gcdt.logger import setup_logger
from gcdt.s3 import _bucket_exists

from .helpers_aws import awsclient  # fixture!
from . import helpers

log = setup_logger(__name__)


# TODO move me back to helpers_aws!!
# bucket helpers (parts borrowed from tenkai)
def create_bucket(awsclient, bucket):
    client = awsclient.get_client('s3')
    client.create_bucket(
        Bucket=bucket,
        CreateBucketConfiguration={
            'LocationConstraint': 'eu-west-1'
        }
    )


def delete_bucket(awsclient, bucket):
    log.debug('deleting bucket %s' % bucket)
    if bucket.startswith('unittest-'):
        s3 = awsclient.get_client('s3')
        # delete all objects first
        # TODO
        # bu = s3.Bucket(bucket)
        # log.debug('deleting keys')
        # for key in bu.objects.all():
        #    log.debug('deleting key: %s' % key)
        #    key.delete()
        #    s3.delete_object(Bucket=bucket, Key='foo')

        log.debug('deleting bucket')
        # now we can delete the bucket
        s3.delete_bucket(Bucket=bucket)


@pytest.fixture(scope='function')  # 'function' or 'module'
def temp_bucket(awsclient):
    # create a bucket
    temp_string = helpers.random_string()
    bucket_name = 'unittest-lambda-s3-event-source-%s' % temp_string
    create_bucket(awsclient, bucket_name)
    yield bucket_name
    # cleanup
    delete_bucket(awsclient, bucket_name)


def test_bucket_exists(awsclient, temp_bucket):
    assert _bucket_exists(awsclient, temp_bucket)


def test_bucket_does_not_exist(awsclient):
    temp_string = helpers.random_string()
    bucket_name = 'unittest-lambda-s3-event-source-%s' % temp_string
    assert not _bucket_exists(awsclient, bucket_name)
