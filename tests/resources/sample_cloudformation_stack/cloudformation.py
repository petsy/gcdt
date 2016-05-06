#!/usr/bin/env python

import os
import troposphere
from troposphere import ec2

# Converted from S3_Bucket.template located at:
# http://aws.amazon.com/cloudformation/aws-cloudformation-templates/

from troposphere import Output, Ref, Template
from troposphere.s3 import Bucket, PublicRead
from resources import sample_hook

# TODO
# ramuda cookiecutter
# add resources folder to kumo for post_hook stuff
# add lambda to post_hook folder
# call lambda_deploy, lambda_invoke_lambda_delete from folder


t = Template()

t.add_description(
    "AWS CloudFormation Sample Template S3_Bucket: template showing "
    "how to create a publicly accessible S3 bucket."
)

s3bucket = t.add_resource(Bucket("S3Bucket", AccessControl=PublicRead, ))
s3bucket1 = t.add_resource(Bucket("S3Bucket1", AccessControl=PublicRead, ))
s3bucket2 = t.add_resource(Bucket("S3Bucket2", AccessControl=PublicRead, ))

t.add_output(Output(
    "BucketName",
    Value=Ref(s3bucket),
    Description="Name of S3 bucket"
))


def generate_template():
    return t.to_json()


def post_hook():
    sample_hook.post_hook()


def post_update_hook():
    print("i'm a post update hook")


def post_create_hook():
    print("i'm a post create hook")
