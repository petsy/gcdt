import os
import sys

import boto3
from docopt import docopt
from gcdt.config_reader import read_config
from gcdt import monitoring
import json
from tabulate import tabulate
import sys
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


def deploy(applicationName, deploymentGroupName, deploymentConfigName, bucket, key="bundle.zip"):
    bundle_revision()
    etag, version = upload_revision_to_s3("jobr-codedeploy-test")

    client = boto3.client("codedeploy")
    response = client.create_deployment(
        applicationName=applicationName,
        deploymentGroupName=deploymentGroupName,
        revision={
            'revisionType': 'S3',
            's3Location': {
                'bucket': bucket,
                'key': key,
                'bundleType': 'zip',
                'eTag': etag,
                'version': version,
            },
        },
        deploymentConfigName=deploymentConfigName,
        description='deploy with tenkai',
        ignoreApplicationStopFailures=True
    )


def create_application_revision():
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


def bundle_revision():
    zip = tenkai_utils.make_zip_file_bytes(path=".")
    f = open('/tmp/bundle.zip', 'wb')
    f.write(zip)
    f.close()


def upload_revision_to_s3(bucket, file="/tmp/bundle.zip"):
    client = boto3.client('s3')
    transfer = S3Transfer(client)
    # Upload /tmp/myfile to s3://bucket/key and print upload progress.
    transfer.upload_file(file, bucket, 'bundle.zip',
                         callback=ProgressPercentage(file))
    response = client.head_object(Bucket=bucket, Key="bundle.zip")
    print "\n"
    print response["ETag"]
    print response["VersionId"]
    return response["ETag"], response["VersionId"]


def main():
    arguments = docopt(doc)
    conf = None

    # Run command
    if arguments["deploy"]:
        env = (arguments["--env"] if arguments["--env"] else "DEV")
        # conf = get_config(arguments)
        # are_credentials_still_valid()
        deploy(applicationName="mep-dev-cms-stack-mediaExchangeCms-1D3UDZRQ0I65J",
               deploymentGroupName="mep-dev-cms-stack-mediaExchangeCmsDg-1UHT4YWDAGNQJ",
               deploymentConfigName="CodeDeployDefaultemplate.AllAtOnce0", bucket="jobr-codedeploy-test")
    if arguments["bundle"]:
        bundle_revision()
    if arguments["push"]:
        bundle_revision()
        upload_revision_to_s3("jobr-codedeploy-test")


if __name__ == '__main__':
    main()
