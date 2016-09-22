# Converted from EC2InstanceSample.template located at:
# http://aws.amazon.com/cloudformation/aws-cloudformation-templates/
import random
import string
from troposphere import Base64, FindInMap, GetAtt
from troposphere import Parameter, Output, Ref, Template
from troposphere.iam import InstanceProfile
from troposphere.codedeploy import (
    Ec2TagFilters,
    Application,
    DeploymentConfig,
    DeploymentGroup,
    MinimumHealthyHosts,
    S3Location,
)
import troposphere.ec2 as ec2
from gcdt.iam import IAMRoleAndPolicies
# since application is defined based on name-tag we don't want matching names
random_string = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(7))
NAME_TAG = 'gcdt-test-tenkai-deployment_' + random_string

template = Template()

# Instantiate helper
iam_ec2 = IAMRoleAndPolicies(template, 'instance-role-', ['ec2.amazonaws.com'], '/ec2/')

# role
name = 'tenkaiTest'
role_ec2 = iam_ec2.build_role(name)
iam_ec2.build_policy(
    name,
    [
        { # S3 - CodeDeploy
            'Effect': 'Allow',
            'Action': [
                's3:Get*',
                's3:List*',
            ],
            'Resource': 'arn:aws:s3:::7finity-dp-dev-deployment/*',

        },
    ],
    [
        Ref(role_ec2)
    ]
)

# EC2 - InstanceProfile (Role to run everything)
instance_role_profile = template.add_resource(InstanceProfile(
    "InstanceRoleProfileJenkins",
    Path='/ec2/',
    Roles=[
        Ref(role_ec2)
    ]
))


ec2_instance = template.add_resource(ec2.Instance(
    "Ec2Instance",
    ImageId="ami-25681456",
    InstanceType="t2.micro",
    KeyName='dev-ec2',
    SecurityGroupIds=["sg-c8bce3ac"]

    , # hard coded to glomex default sg
    SubnetId='subnet-feb7ac9b', # hard coded to glomex subnet eu-west-1a
    UserData=Base64("80"),
    IamInstanceProfile=Ref(instance_role_profile),
    Monitoring=True,
    Tags=[
        ec2.Tag('Name', NAME_TAG)
    ]
))


########
# CodeDeploy Roles
##

iam = IAMRoleAndPolicies(template, 'codedeploy-', ["codedeploy.us-east-1.amazonaws.com",
                                            "codedeploy.us-west-2.amazonaws.com",
                                            "codedeploy.eu-west-1.amazonaws.com",
                                            "codedeploy.ap-southeast-2.amazonaws.com"], '/')

role_name = "CodeDeployTrustRole"
role_code_deploy_trust_role = iam.build_role(
    role_name
)

CodeDeployPolicyName = "CodeDeployRolePolicies"
CodeDeployRolePolicies = iam.build_policy(
    CodeDeployPolicyName,
    [
        {
            "Effect": "Allow",
            "Resource": [
                "*"
            ],
            "Action": [
                "ec2:Describe*"
            ]
        },
    ],
    [
        Ref(role_code_deploy_trust_role)
    ]

)

app = template.add_resource(Application('gcdtTenkaiTestingApp'))


# CreateDeploymentGroup using applicationName as input and deploymentConfigName
depgroup = template.add_resource(
    DeploymentGroup(
        "gcdtTestDeploymentGroup",
        ApplicationName=Ref(app),
        ServiceRoleArn=GetAtt(role_code_deploy_trust_role, "Arn"),
        Ec2TagFilters=[
            Ec2TagFilters(
                Key='Name',
                Value=NAME_TAG,
                Type='KEY_AND_VALUE'
            )
        ]
    )
)

template.add_output([
    Output(
        "InstanceName",
        Description="InstanceId of the newly created EC2 instance",
        Value=NAME_TAG,
    ),
    Output(
        "InstanceId",
        Description="InstanceId of the newly created EC2 instance",
        Value=Ref(ec2_instance),
    ),
    Output(
        'DeploymentGroupName',
        Description='Name of the DeploymentGroup',
        Value=Ref(depgroup)
    ),
    Output(
        'ApplicationName',
        Description='Name of the App',
        Value=Ref(app)
    ),
])

def generate_template():
    return template.to_json()