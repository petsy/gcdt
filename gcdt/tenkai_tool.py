# pylint: disable=E0401, E1101

import sys
import boto3
from docopt import docopt
from glomex_utils.config_reader import read_config
import time
from clint.textui import colored
import tenkai_utils
#from s3transfer import S3Transfer
from boto3.s3.transfer import S3Transfer
import utils

doc = """Usage:
        tenkai bundle
        tenkai deploy
        tenkai version

-h --help           show this
"""

CONFIG_KEY = "codedeploy"


def are_credentials_still_valid():
    client = boto3.client("lambda")
    try:
        client.list_functions()
    except Exception as e:
        print colored.red("Your credentials have expired... Please renew and try again!")
        sys.exit(1)
    else:
        pass


def deploy(applicationName, deploymentGroupName, deploymentConfigName, bucket):
    bundlefile = bundle_revision()
    etag, version = upload_revision_to_s3(bucket, applicationName, bundlefile)

    client = boto3.client("codedeploy")
    response = client.create_deployment(
        applicationName=applicationName,
        deploymentGroupName=deploymentGroupName,
        revision={
            'revisionType': 'S3',
            's3Location': {
                'bucket': bucket,
                'key': build_bundle_key(applicationName),
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
    """
    wait until an deployment is in an steady state and output information
    """
    counter = 0
    steady_states = ['Succeeded', 'Failed', 'Stopped']
    client = boto3.client("codedeploy")
    while counter <= iterations:
        response = client.get_deployment(deploymentId=deploymentId)
        status = response['deploymentInfo']['status']
        if status not in steady_states:
            print "Deployment: %s - State: %s" % (deploymentId, status)
            sys.stdout.flush()
            time.sleep(10)
        elif status is 'Failed':
            print colored.red(
                "Deployment: %s failed: %s" % (deploymentId, response['deploymentInfo']['errorInformation']))
            sys.exit(1)
        else:
            print "Deployment: %s - State: %s" % (deploymentId, status)
            break


def bundle_revision(outputpath='/tmp'):
    tarfile_name = tenkai_utils.make_tar_file(path="./codedeploy", outputpath=outputpath)
    return tarfile_name


def upload_revision_to_s3(bucket, applicationName, file):
    client = boto3.client('s3')
    transfer = S3Transfer(client)
    # Upload /tmp/myfile to s3://bucket/key and print upload progress.
    transfer.upload_file(file, bucket, build_bundle_key(applicationName))
    response = client.head_object(Bucket=bucket, Key=build_bundle_key(applicationName))
    # print "\n"
    # print response["ETag"]
    # print response["VersionId"]
    return response["ETag"], response["VersionId"]


def bucket_exists(bucket):
    s3 = boto3.resource('s3')
    return s3.Bucket(bucket) in s3.buckets.all()


def create_bucket(bucket):
    client = boto3.client("s3")
    client.create_bucket(
        Bucket=bucket
    )
    client.put_bucket_versioning(
        Bucket=bucket,
        VersioningConfiguration={
            'Status': 'Enabled'
        }
    )


def build_bundle_key(application_name):
    key = application_name + "/" + "bundle.tar.gz"
    return key


def prepare_artifacts_bucket(bucket):
    if not bucket_exists(bucket):
        create_bucket(bucket)
    else:
        pass


def main():
    arguments = docopt(doc)

    # Run command
    if arguments["deploy"]:
        conf = read_config(config_base_name="codedeploy")

        # are_credentials_still_valid()
        prepare_artifacts_bucket(conf.get("codedeploy.artifactsBucket"))
        deployment = deploy(
            applicationName=conf.get("codedeploy.applicationName"),
            deploymentGroupName=conf.get("codedeploy.deploymentGroupName"),
            deploymentConfigName=conf.get("codedeploy.deploymentConfigName"),
            bucket=conf.get("codedeploy.artifactsBucket")
        )
        deployment_status(deployment)
    elif arguments["bundle"]:
        conf = read_config(config_base_name="codedeploy")
        print "created bundle at %s"% bundle_revision()
    elif arguments["version"]:
        utils.version()


if __name__ == '__main__':
    main()
