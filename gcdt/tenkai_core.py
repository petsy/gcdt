# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import sys
import json
import time
import tarfile
import boto3
import subprocess
from boto3.s3.transfer import S3Transfer
from clint.textui import colored


def deploy(applicationName, deploymentGroupName, deploymentConfigName, bucket, pre_bundle_scripts=None):
    """Upload bundle and deploy to deployment group.
    This includes the bundle-action.

    :param applicationName:
    :param deploymentGroupName:
    :param deploymentConfigName:
    :param bucket:
    :return: deploymentId from create_deployment
    """
    print('%s\n%s\n%s' % (applicationName, deploymentGroupName, deploymentConfigName))
    if pre_bundle_scripts:
        exit_code = _execute_pre_bundle_scripts(pre_bundle_scripts)
        if exit_code != 0:
            print('Pre bundle script exited with error')
            sys.exit(1)
    bundlefile = bundle_revision()
    etag, version = _upload_revision_to_s3(bucket, applicationName, bundlefile)

    client = boto3.client('codedeploy')
    response = client.create_deployment(
        applicationName=applicationName,
        deploymentGroupName=deploymentGroupName,
        revision={
            'revisionType': 'S3',
            's3Location': {
                'bucket': bucket,
                'key': _build_bundle_key(applicationName),
                'bundleType': 'tgz',
                'eTag': etag,
                'version': version,
            },
        },
        deploymentConfigName=deploymentConfigName,
        description='deploy with tenkai',
        ignoreApplicationStopFailures=True
    )
    return response['deploymentId']


def deployment_status(deploymentId, iterations=100):
    """Wait until an deployment is in an steady state and output information.

    :param deploymentId:
    :param iterations:
    :return: exit_code
    """
    counter = 0
    steady_states = ['Succeeded', 'Failed', 'Stopped']
    client = boto3.client('codedeploy')

    while counter <= iterations:
        response = client.get_deployment(deploymentId=deploymentId)
        status = response['deploymentInfo']['status']

        if status not in steady_states:
            print('Deployment: %s - State: %s' % (deploymentId, status))
            sys.stdout.flush()
            time.sleep(10)
        elif status == 'Failed':
            print(
                colored.red('Deployment: {} failed: {}'.format(
                    deploymentId,
                    json.dumps(response['deploymentInfo']['errorInformation'], indent=2)
                ))
            )
            # sys.exit(1)
            return 1
        else:
            print('Deployment: %s - State: %s' % (deploymentId, status))
            break

    return 0


def bundle_revision(outputpath='/tmp'):
    """Prepare the tarfile for the revision.

    :param outputpath:
    :return: tarfile_name
    """
    tarfile_name = _make_tar_file(path='./codedeploy',
                                  outputpath=outputpath)
    return tarfile_name


def prepare_artifacts_bucket(bucket):
    """Prepare the bucket if it does not exist.

    :param bucket:
    """
    if not _bucket_exists(bucket):
        _create_bucket(bucket)


def _upload_revision_to_s3(bucket, applicationName, file):
    client = boto3.client('s3')
    transfer = S3Transfer(client)
    # Upload /tmp/myfile to s3://bucket/key and print upload progress.
    transfer.upload_file(file, bucket, _build_bundle_key(applicationName))
    response = client.head_object(Bucket=bucket,
                                  Key=_build_bundle_key(applicationName))

    return response['ETag'], response['VersionId']

def _execute_pre_bundle_scripts(scripts):
    for script in scripts:
        exit_code = _execute_script(script)
        if exit_code != 0:
            return exit_code
    return 0

def _execute_script(file_name):
    if os.path.isfile(file_name):
        print('Executing %s ...' % file_name)
        exit_code = subprocess.call([file_name, '-e'])
        return exit_code
    else:
        print('No file found matching %s...' % file_name)
        return 1


def _bucket_exists(bucket):
    s3 = boto3.resource('s3')
    return s3.Bucket(bucket) in s3.buckets.all()


def _create_bucket(bucket):
    client = boto3.client('s3')
    client.create_bucket(
        Bucket=bucket
    )
    client.put_bucket_versioning(
        Bucket=bucket,
        VersioningConfiguration={
            'Status': 'Enabled'
        }
    )


def _build_bundle_key(application_name):
    return '%s/bundle.tar.gz' % application_name


def _files_to_bundle(path):
    for root, dirs, files in os.walk(path):
        for f in files:
            full_path = os.path.join(root, f)
            archive_name = full_path[len(path) + len(os.sep):]
            # print "full_path, archive_name" + full_path, archive_name
            yield full_path, archive_name


def _make_tar_file(path, outputpath):
    # make sure we add a unique identifier when we are running within jenkins
    file_suffix = os.getenv('BUILD_TAG', '')
    destfile = '%s/tenkai-bundle%s.tar.gz' % (outputpath, file_suffix)
    with tarfile.open(destfile, 'w:gz') as tar:
        for full_path, archive_name in _files_to_bundle(path=path):
            tar.add(full_path, recursive=False, arcname=archive_name)
    return destfile
