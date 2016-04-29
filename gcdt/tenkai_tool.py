#pylint: disable=E0401
import os
import sys

import boto3
from docopt import docopt
from gcdt.config_reader import read_config
import time
from gcdt import monitoring
import json
from tabulate import tabulate
from clint.textui import colored
import uuid
from cookiecutter.main import cookiecutter
# from selenium import webdriver
import random
import string
import tenkai_utils
from s3transfer import S3Transfer
from tenkai_utils import ProgressPercentage


doc = """Usage:
        tenkai deploy [-e ENV]
        tenkai bundle
        tenkai push
        tenkai list
        tenkai delete -f [-e ENV]
        tenkai generate [-e ENV]
        tenkai validate [-e ENV]
        tenkai scaffold [<stackname>]
        tenkai configure
        tenkai preview

-e ENV --env ENV    environment to use [default: dev] else is prod
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


def config_from_file(env):
    os.environ['ENV'] = env

    # read config from given name
    return read_config()


def get_config(arguments):
    if arguments['--env'] == 'prod':
        conf = config_from_file('PROD')
    else:
        conf = config_from_file('DEV')

    return conf


def deploy(applicationName, deploymentGroupName, deploymentConfigName, bucket):
    bundle_revision()
    etag, version = upload_revision_to_s3(bucket, applicationName)

    client = boto3.client("codedeploy")
    response = client.create_deployment(
        applicationName=applicationName,
        deploymentGroupName=deploymentGroupName,
        revision={
            'revisionType': 'S3',
            's3Location': {
                'bucket': bucket,
                'key': build_bundle_key(applicationName),
                'bundleType': 'zip',
                'eTag': etag,
                'version': version,
            },
        },
        deploymentConfigName=deploymentConfigName,
        description='deploy with tenkai',
        ignoreApplicationStopFailures=True
    )
    return response['deploymentId']


def create_application_revision():
    # UNUSED???
    client = boto3.client("codedeploy")
    response = client.register_application_revision(
        applicationName='string',
        description='string',
        revision={
            'revisionType': 'S3' | 'GitHub',
            's3Location': {
                'bucket': 'string',
                'key': 'string',
                'bundleType': 'tar' | 'tgz' | 'zip',
                'version': 'string',
                'eTag': 'string',
                'version': version,
            },
            'gitHubLocation': {
                'repository': 'string',
                'commitId': 'string'
            }
        }
    )

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
            time.sleep(10)
        elif status is 'Failed':
            print "Deployment: %s failed: %s" % (deploymentId, response['deploymentInfo']['errorInformation'])
            sys.exit(1)
        else:
            print "Deployment: %s - State: %s" % (deploymentId, status)
            break


def bundle_revision():
    zip = tenkai_utils.make_zip_file_bytes(path="./codedeploy")
    f = open('/tmp/bundle.zip', 'wb')
    f.write(zip)
    f.close()


def upload_revision_to_s3(bucket, applicationName, file="/tmp/bundle.zip"):
    client = boto3.client('s3')
    transfer = S3Transfer(client)
    # Upload /tmp/myfile to s3://bucket/key and print upload progress.
    transfer.upload_file(file, bucket, build_bundle_key(applicationName))
    response = client.head_object(Bucket=bucket, Key=build_bundle_key(applicationName))
    print "\n"
    print response["ETag"]
    print response["VersionId"]
    return response["ETag"], response["VersionId"]


def bucket_exists(bucket):
    s3 = boto3.resource('s3')
    return s3.Bucket(bucket) in s3.buckets.all()


def create_bucket(bucket):
    client = boto3.client("s3")
    response = client.create_bucket(
        Bucket=bucket)
    response = client.put_bucket_versioning(
        Bucket=bucket,
        VersioningConfiguration={
            'Status': 'Enabled'
        }
    )

def build_bundle_key(applicationName):
    key = applicationName+"/"+"bundle.zip"
    return key

def prepare_artifacts_bucket(bucket):
    if not bucket_exists(bucket):
        create_bucket(bucket)
    else:
        pass

def main():
    arguments = docopt(doc)
    conf = None

    # Run command
    if arguments["deploy"]:
        env = (arguments["--env"] if arguments["--env"] else "DEV")
        # conf = get_config(arguments)
        conf = read_config(config_base_name="codedeploy")
        # are_credentials_still_valid()
        prepare_artifacts_bucket(conf.get("codedeploy.artifactsBucket"))
        deployment = deploy(applicationName=conf.get("codedeploy.applicationName"),
               deploymentGroupName=conf.get("codedeploy.deploymentGroupName"),
               deploymentConfigName=conf.get("codedeploy.deploymentConfigName"),
               bucket=conf.get("codedeploy.artifactsBucket"))
    if arguments["bundle"]:
        bundle_revision()
    if arguments["push"]:
        conf = read_config(config_base_name="codedeploy")
        bundle_revision()
        upload_revision_to_s3(conf.get("codedeploy.artifactsBucket"), conf.get("codedeploy.applicationName"))
        deployment_status(deployment)


if __name__ == '__main__':
    main()
