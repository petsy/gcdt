# -*- coding: utf-8 -*-
from __future__ import print_function

import json
import time
import boto3
from gcdt.logger import setup_logger
from gcdt.ramuda_core import deploy_lambda

log = setup_logger(__name__)


# bucket helpers (parts borrowed from tenkai)
def create_bucket(bucket):
    client = boto3.client('s3')
    client.create_bucket(
        Bucket=bucket,
        CreateBucketConfiguration={
            'LocationConstraint': 'eu-west-1'
        }
    )


def delete_bucket(bucket):
    log.debug('deleting bucket %s' % bucket)
    if bucket.startswith('unittest-'):
        s3 = boto3.resource('s3')
        # delete all objects first
        bu = s3.Bucket(bucket)
        log.debug('deleting keys')
        for key in bu.objects.all():
            log.debug('deleting key: %s' % key)
            key.delete()
        log.debug('deleting bucket')
        # now we can delete the bucket
        bu.delete()


# lambda helpers
def create_lambda_role_helper(role_name):
    # caller needs to clean up both role!
    role = create_role_helper(
        role_name,
        policies=[
            'arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole',
            'arn:aws:iam::aws:policy/AWSLambdaExecute']
    )
    return role['Arn']


def create_lambda_helper(lambda_name, role_arn, handler_filename,
                         lambda_handler='handler.handle'):
    # caller needs to clean up both lambda!
    '''
    role = _create_role(
        role_name,
        policies=[
            'arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole',
            'arn:aws:iam::aws:policy/AWSLambdaExecute']
    )

    role_arn = role['Arn']
    '''
    lambda_description = 'lambda created for unittesting ramuda deployment'
    # lambda_handler = 'handler.handle'
    timeout = 300
    memory_size = 128
    folders_from_file = [
        {'source': './vendored', 'target': '.'},
        {'source': './impl', 'target': 'impl'}
    ]
    artifact_bucket = None

    # create the function
    deploy_lambda(function_name=lambda_name,
                  role=role_arn,
                  handler_filename=handler_filename,
                  handler_function=lambda_handler,
                  folders=folders_from_file,
                  description=lambda_description,
                  timeout=timeout,
                  memory=memory_size,
                  artifact_bucket=artifact_bucket)
    time.sleep(10)


# role helpers
def delete_role_helper(role_name):
    """Delete the testing role.

    :param role: the temporary role that has been created via _create_role
    """
    # role_name = role['RoleName']
    iam = boto3.client('iam')
    roles = [r['RoleName'] for r in iam.list_roles()['Roles']]
    if role_name in roles:
        # detach all policies first
        policies = iam.list_attached_role_policies(RoleName=role_name)
        for p in policies['AttachedPolicies']:
            response = iam.detach_role_policy(
                RoleName=role_name,
                PolicyArn=p['PolicyArn']
            )

        # delete the role
        response = iam.delete_role(RoleName=role_name)


def create_role_helper(name, policies=None):
    """Create a role with an optional inline policy """
    iam = boto3.client('iam')
    policy_doc = {
        'Version': '2012-10-17',
        'Statement': [
            {
                'Effect': 'Allow',
                'Principal': {'Service': ['lambda.amazonaws.com']},
                'Action': ['sts:AssumeRole']
            },
        ]
    }
    roles = [r['RoleName'] for r in iam.list_roles()['Roles']]
    if name in roles:
        print('IAM role %s exists' % name)
        role = iam.get_role(RoleName=name)['Role']
    else:
        print('Creating IAM role %s' % name)
        role = iam.create_role(
            RoleName=name,
            AssumeRolePolicyDocument=json.dumps(policy_doc)
        )['Role']

    # attach managed policy
    if policies is not None:
        for p in policies:
            iam.attach_role_policy(RoleName=role['RoleName'], PolicyArn=p)

    # TODO: on 20160816 we had multiple times that the role could not be assigned
    # we suspect that this is a timing issue with AWS lambda
    # get_role to make sure role is available for lambda
    # response = iam.list_attached_role_policies(RoleName=name)
    # log.info('created role: %s' % name)
    # log.info(response)
    # ClientError: An error occurred (InvalidParameterValueException) when
    # calling the CreateFunction operation: The role defined for the function
    # cannot be assumed by Lambda.
    # current assumption is that the role is not propagated to lambda in time
    time.sleep(15)

    return role