# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import sys
import json
import time
import tarfile

from boto3.s3.transfer import S3Transfer
from clint.textui import colored

from gcdt import monitoring, utils


def deploy(boto_session, applicationName, deploymentGroupName, deploymentConfigName, bucket,
           slack_token=None, slack_channel='systemmessages',
           pre_bundle_scripts=None):
    """Upload bundle and deploy to deployment group.
    This includes the bundle-action.

    :param applicationName:
    :param deploymentGroupName:
    :param deploymentConfigName:
    :param bucket:
    :param slack_token:
    :param slack_channel:
    :return: deploymentId from create_deployment
    """
    if pre_bundle_scripts:
        exit_code = utils.execute_scripts(pre_bundle_scripts)
        if exit_code != 0:
            print('Pre bundle script exited with error')
            sys.exit(1)
    bundlefile = bundle_revision()
    etag, version = _upload_revision_to_s3(boto_session, bucket,
                                           applicationName, bundlefile)

    client_codedeploy = boto_session.client('codedeploy')
    response = client_codedeploy.create_deployment(
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

    print("Deployment: {} -> URL: https://{}.console.aws.amazon.com/codedeploy/home?region={}#/deployments/{}".format(
        response['deploymentId'],
        boto_session.region_name,
        boto_session.region_name,
        response['deploymentId'],
    ))

    message = 'tenkai bot: deployed deployment group %s ' % deploymentGroupName
    monitoring.slack_notification(slack_channel, message, slack_token)

    return response['deploymentId']


def deployment_status(boto_session, deploymentId, iterations=100):
    """Wait until an deployment is in an steady state and output information.

    :param deploymentId:
    :param iterations:
    :return: exit_code
    """
    counter = 0
    steady_states = ['Succeeded', 'Failed', 'Stopped']
    client_codedeploy = boto_session.client('codedeploy')

    while counter <= iterations:
        response = client_codedeploy.get_deployment(deploymentId=deploymentId)
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


def prepare_artifacts_bucket(boto_session, bucket):
    """Prepare the bucket if it does not exist.

    :param bucket:
    """
    if not _bucket_exists(boto_session, bucket):
        _create_bucket(boto_session, bucket)


def _upload_revision_to_s3(boto_session, bucket, applicationName, file):
    client_s3 = boto_session.client('s3')
    transfer = S3Transfer(client_s3)
    # Upload /tmp/myfile to s3://bucket/key and print upload progress.
    transfer.upload_file(file, bucket, _build_bundle_key(applicationName))
    response = client_s3.head_object(Bucket=bucket,
                                  Key=_build_bundle_key(applicationName))

    return response['ETag'], response['VersionId']


def _bucket_exists(boto_session, bucket):
    client_s3 = boto_session.resource('s3')
    return client_s3.Bucket(bucket) in client_s3.buckets.all()


def _create_bucket(boto_session, bucket):
    client_s3 = boto_session.client('s3')
    client_s3.create_bucket(
        Bucket=bucket
    )
    client_s3.put_bucket_versioning(
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
