# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

import pytest

from gcdt.logger import setup_logger
from gcdt.s3 import _bucket_exists, upload_file_to_s3, ls

from .helpers_aws import awsclient  # fixtures!
from .helpers import random_file  # fixtures!
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
    # this works up to 1000 keys
    log.debug('deleting bucket %s' % bucket)
    if bucket.startswith('unittest-'):
        client_s3 = awsclient.get_client('s3')
        # delete all objects first
        log.debug('deleting keys')
        objects = client_s3.list_objects_v2(Bucket=bucket)
        if objects['KeyCount'] > 0:
            delete={'Objects': [{'Key': k['Key']} for k in objects['Contents']]}
            client_s3.delete_objects(Bucket=bucket, Delete=delete)

        log.debug('deleting bucket')
        # now we can delete the bucket
        client_s3.delete_bucket(Bucket=bucket)


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


def test_upload_file_to_s3(awsclient, temp_bucket, random_file):
    upload_file_to_s3(awsclient, temp_bucket, 'content.txt', random_file)
    assert 'content.txt' in ls(awsclient, temp_bucket)
