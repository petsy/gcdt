#!/usr/bin/env python

import troposphere

# Converted from S3_Bucket.template located at:
# http://aws.amazon.com/cloudformation/aws-cloudformation-templates/
import json
from troposphere import Output, Ref, Template
from troposphere.s3 import Bucket, PublicRead


t = Template()

t.add_description(
    "AWS CloudFormation Sample Template S3_Bucket: template showing "
    "how to create a publicly accessible S3 bucket."
)

s3bucket1 = t.add_resource(Bucket("S3Bucket1", AccessControl=PublicRead, ))

t.add_output(Output(
    "BucketName",
    Value=Ref(s3bucket1),
    Description="Name of S3 bucket"
))

param_foo = t.add_parameter(troposphere.Parameter(
    'InstanceType',
    Description='Type of EC2 instance',
    Type='String',
))


def generate_template():
    return t.to_json()


def get_stack_policy():
    return json.dumps({
          "Statement" : [
            {
              "Effect" : "Allow",
              "Action" : "Update:Modify",
              "Principal": "*",
              "Resource" : "*"
            },
            {
              "Effect" : "Deny",
              "Action" : ["Update:Replace", "Update:Delete"],
              "Principal": "*",
              "Resource" : "*"
            }
          ]
        })

COUNTER = {
    'register': 0,
    'deregister': 0,
}


def register():
    COUNTER['register'] += 1


def deregister():
    COUNTER['deregister'] += 1
