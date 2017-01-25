#!/usr/bin/env python

from troposphere import Base64, FindInMap, GetAtt
from troposphere import Parameter, Output, Ref, Template
import troposphere.ec2 as ec2


template = Template()

template.add_mapping('RegionMap', {
    "us-east-1": {"AMI": "ami-7f418316"},
    "us-west-1": {"AMI": "ami-951945d0"},
    "us-west-2": {"AMI": "ami-16fd7026"},
    "eu-west-1": {"AMI": "ami-24506250"},
    "sa-east-1": {"AMI": "ami-3e3be423"},
    "ap-southeast-1": {"AMI": "ami-74dda626"},
    "ap-northeast-1": {"AMI": "ami-dcfa4edd"}
})

# TODO: 'subnet-feb7ac9b' is a problem since the test can now only run on the
# dp account
ec2_instance = template.add_resource(ec2.Instance(
    "Ec2Instance",
    ImageId='ami-25681456',
    InstanceType='t2.micro',
    KeyName='dev-ec2',
    SecurityGroupIds=["sg-8eec36e8"],  # hard coded to glomex default sg
    SubnetId='subnet-b6eaa5d2',  # hard coded to glomex subnet eu-west-1a
    UserData=Base64("80"),
    Tags=[
        ec2.Tag('Name', 'gcdt-test-ec2-ebs-tagging')
    ]
    ))

template.add_output([
    Output(
        "InstanceId",
        Description="InstanceId of the newly created EC2 instance",
        Value=Ref(ec2_instance),
    ),
])


def generate_template():
    return template.to_json()

