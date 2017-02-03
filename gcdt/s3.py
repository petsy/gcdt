# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

from s3transfer import S3Transfer
from botocore.client import ClientError


def upload_file_to_s3(awsclient, bucket, key, file):
    """Upload a file to AWS S3 bucket.

    :param awsclient:
    :param bucket:
    :param key:
    :param file:
    :return:
    """
    client_s3 = awsclient.get_client('s3')
    transfer = S3Transfer(client_s3)
    # Upload /tmp/myfile to s3://bucket/key and print upload progress.
    transfer.upload_file(file, bucket, key)
    response = client_s3.head_object(Bucket=bucket, Key=key)

    return response['ETag'], response['VersionId']


def prepare_artifacts_bucket(awsclient, bucket):
    """Prepare the bucket if it does not exist.

    :param bucket:
    """
    if not _bucket_exists(awsclient, bucket):
        _create_bucket(awsclient, bucket)


def _bucket_exists(awsclient, bucket):
    #client_s3 = awsclient.resource('s3')
    client_s3 = awsclient.get_client('s3')
    # TODO test to make sure this really works !!!!!
    #return client_s3.Bucket(bucket) in client_s3.buckets.all()
    try:
        client_s3.head_bucket(Bucket=bucket)
        return True
    except ClientError:
        return False


def _create_bucket(awsclient, bucket):
    client_s3 = awsclient.get_client('s3')
    client_s3.create_bucket(
        Bucket=bucket
    )
    client_s3.put_bucket_versioning(
        Bucket=bucket,
        VersioningConfiguration={
            'Status': 'Enabled'
        }
    )
