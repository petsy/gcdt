#!/usr/bin/env python

from troposphere import Base64, FindInMap, GetAtt
from troposphere import Parameter, Output, Ref, Template
import troposphere.ec2 as ec2


from troposphere import Base64, Join
from troposphere import Parameter, Ref, Template
from troposphere import cloudformation, autoscaling
from troposphere.autoscaling import AutoScalingGroup, Tag
from troposphere.autoscaling import LaunchConfiguration
from troposphere.policies import (
    AutoScalingReplacingUpdate, AutoScalingRollingUpdate, UpdatePolicy
)


t = Template()

t.add_description("""\
Configures autoscaling group for api app""")


t.add_mapping('RegionMap', {
    "us-east-1": {"AMI": "ami-7f418316"},
    "us-west-1": {"AMI": "ami-951945d0"},
    "us-west-2": {"AMI": "ami-16fd7026"},
    "eu-west-1": {"AMI": "ami-24506250"},
    "sa-east-1": {"AMI": "ami-3e3be423"},
    "ap-southeast-1": {"AMI": "ami-74dda626"},
    "ap-northeast-1": {"AMI": "ami-dcfa4edd"}
})


LaunchConfiguration = t.add_resource(LaunchConfiguration(
    'LaunchConfiguration',
    UserData=Base64(Join('', [
        '#!/bin/bash\n',
        'cfn-signal -e 0',
        '    --resource AutoscalingGroup',
        '    --stack ', Ref('AWS::StackName'),
        '    --region ', Ref('AWS::Region'), '\n'
    ])),
    ImageId=FindInMap("RegionMap", Ref("AWS::Region"), "AMI"),
    KeyName='dev-ec2',
    InstanceType='t1.micro',
    SecurityGroups=["sg-c8bce3ac"], # hard coded to glomex default sg
))

as_group = t.add_resource(AutoScalingGroup(
    'AutoscalingGroup',
    DesiredCapacity=1,
    Tags=[
        Tag('Name','gcdt-test-autoscaling-ebs-tagging', True)
    ],
    LaunchConfigurationName=Ref(LaunchConfiguration),
    MinSize='1',
    MaxSize='1',
    VPCZoneIdentifier=['subnet-feb7ac9b'],
    AvailabilityZones=['eu-west-1a'],
    HealthCheckType='EC2'
))
t.add_output(
    Output(
        "AutoScalingGroupName",
        Description="Name of the autoscaling group",
        Value=Ref(as_group),
    ),
)

def generate_template():
    return t.to_json()

