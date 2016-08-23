# -*- coding: utf-8 -*-
from __future__ import print_function
import boto3
from gcdt.logger import setup_logger

log = setup_logger(__name__)


# bucket helpers (parts borrowed from tenkai)
def create_bucket(bucket):
    client = boto3.client('s3')
    client.create_bucket(
        Bucket=bucket,
        CreateBucketConfiguration={
            'LocationConstraint': 'eu-west-1'
        }
    )


def delete_bucket(bucket):
    log.debug('deleting bucket %s' % bucket)
    if bucket.startswith('unittest-'):
        s3 = boto3.resource('s3')
        # delete all objects first
        bu = s3.Bucket(bucket)
        log.debug('deleting keys')
        for key in bu.objects.all():
            log.debug('deleting key: %s' % key)
            key.delete()
        log.debug('deleting bucket')
        # now we can delete the bucket
        bu.delete()
