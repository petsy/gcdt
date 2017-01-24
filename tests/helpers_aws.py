# -*- coding: utf-8 -*-
from __future__ import print_function
import json
import os
import textwrap
import time
import datetime
from io import BytesIO
from requests.structures import CaseInsensitiveDict

import boto3
from botocore.response import StreamingBody
import pytest
import placebo

from gcdt.logger import setup_logger
from gcdt.ramuda_core import deploy_lambda
from . import helpers

log = setup_logger(__name__)


def here(p): return os.path.join(os.path.dirname(__file__), p)


# bucket helpers (parts borrowed from tenkai)
def create_bucket(session, bucket):
    client = session.client('s3')
    client.create_bucket(
        Bucket=bucket,
        CreateBucketConfiguration={
            'LocationConstraint': 'eu-west-1'
        }
    )


def delete_bucket(session, bucket):
    log.debug('deleting bucket %s' % bucket)
    if bucket.startswith('unittest-'):
        s3 = session.resource('s3')
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
def create_lambda_role_helper(boto_session, role_name):
    # caller needs to clean up both role!
    role = create_role_helper(
        boto_session, role_name,
        policies=[
            'arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole',
            'arn:aws:iam::aws:policy/AWSLambdaExecute']
    )
    return role['Arn']


def settings_requirements():
    settings_file = os.path.join('settings_dev.conf')
    with open(settings_file, 'w') as settings:
        setting_string = textwrap.dedent("""\
            sample_lambda {
                cw_name = "dp-dev-sample"
            }""")
        settings.write(setting_string)
    requirements_txt = os.path.join('requirements.txt')
    with open(requirements_txt, 'w') as req:
        req.write('pyhocon==0.3.28\n')
    # ./vendored folder
    if not os.path.exists('./vendored'):
        # reuse ./vendored folder to save us some time during pip install...
        os.makedirs('./vendored')


def create_lambda_helper(boto_session, lambda_name, role_arn, handler_filename,
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
    # prepare ./vendored folder and settings file
    settings_requirements()

    lambda_description = 'lambda created for unittesting ramuda deployment'
    # lambda_handler = 'handler.handle'
    timeout = 300
    memory_size = 128
    folders_from_file = [
        {'source': './vendored', 'target': '.'},
        {'source': './resources/sample_lambda/impl', 'target': 'impl'}
    ]
    artifact_bucket = None

    # create the function
    deploy_lambda(
        boto_session=boto_session,
        function_name=lambda_name,
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
def delete_role_helper(boto_session, role_name):
    """Delete the testing role.

    :param boto_session:
    :param role_name: the temporary role that has been created via _create_role
    """
    # role_name = role['RoleName']
    iam = boto_session.client('iam')
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


def create_role_helper(boto_session, name, policies=None):
    """Create a role with an optional inline policy """
    iam = boto_session.client('iam')
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


def _precond_check():
    """Make sure the default AWS profile is set so the test can run on AWS."""
    if not os.getenv('USER', None).endswith('jenkins') and \
            not os.getenv('AWS_DEFAULT_PROFILE', None):
        print("AWS_DEFAULT_PROFILE variable not set! Test is skipped.")
        return True
    if not os.getenv('ENV', None):
        print("ENV environment variable not set! Test is skipped.")
        return True
    if not os.getenv('ACCOUNT', None):
        print("ACCOUNT environment variable not set! Test is skipped.")
        return True

    return False


# skipif helper check_preconditions
check_preconditions = pytest.mark.skipif(
    _precond_check(),
    reason="Set environment variables to run tests on AWS (see README.md)."
)


@pytest.fixture(scope='function')  # 'function' or 'module'
def cleanup_buckets(boto_session):
    items = []
    yield items
    # cleanup
    for i in items:
        delete_bucket(boto_session, i)


@pytest.fixture(scope='function')  # 'function' or 'module'
def temp_bucket(boto_session):
    # create a bucket
    temp_string = helpers.random_string()
    bucket_name = 'unittest-lambda-s3-event-source-%s' % temp_string
    create_bucket(boto_session, bucket_name)
    yield bucket_name
    # cleanup
    delete_bucket(boto_session, bucket_name)


@pytest.fixture(scope='function')  # 'function' or 'module'
def boto_session(request):
    # details on request: http://programeveryday.com/post/pytest-creating-and-using-fixtures-for-streamlined-testing/
    # store original functions
    random_string_orig = helpers.random_string
    sleep_orig = time.sleep
    random_string_filename = 'random_string.txt'
    prefix = request.module.__name__ + '.' + request.function.__name__
    record_dir = os.path.join(here('./resources/placebo'), prefix)
    if not os.path.exists(record_dir):
        os.makedirs(record_dir)
    session = boto3.session.Session()
    pill = placebo.attach(session, data_path=record_dir)
    if os.getenv('PLACEBO_MODE', '').lower() == 'record':
        # apply the patch
        placebo.pill.serialize = serialize_patch
        placebo.pill.deserialize = deserialize_patch

        pill.record()
        helpers.random_string = recorder(record_dir, random_string_orig,
                                         filename=random_string_filename)
    else:
        def fake_sleep(seconds):
            pass
        helpers.random_string = file_reader(record_dir,
                                            random_string_filename)
        time.sleep = fake_sleep
        pill.playback()
    yield session
    # cleanup
    # restore original functionality
    helpers.random_string = random_string_orig
    time.sleep = sleep_orig


def recorder(record_dir, function, filename=None):
    """this helper wraps a function and writes results to a file
    default filename is the name of the function.

    :param record_dir: where to write the file
    :param function: function to wrap
    :return: wrapped function
    """
    if not filename:
        filename = function.__name__
    if not os.path.exists(record_dir):
        os.makedirs(record_dir)

    def wrapper():
        with open(os.path.join(record_dir, filename), 'a') as rfile:
            result = function()
            print(str(result), file=rfile)
            return result

    return wrapper


def file_reader(record_dir, filename):
    """helper to read a file line by line
    basically same as dfile.next but strips whitespace

    :param record_dir:
    :param filename:
    :return: function that returns a line when called
    """
    path = os.path.join(record_dir, filename)
    if os.path.isfile(path):
        with open(path, 'r') as dfile:
            data = [line.strip() for line in dfile]
            idata = iter(data)

            def f():
                line = next(idata).strip()
                return line
    else:
        # if file does not exist
        def f():
            return ''

    return f


# we need to apply a patch:
# https://github.com/garnaat/placebo/issues/48
def deserialize_patch(obj):
    """Convert JSON dicts back into objects."""
    # Be careful of shallow copy here
    target = dict(obj)
    class_name = None
    if '__class__' in target:
        class_name = target.pop('__class__')
    # Use getattr(module, class_name) for custom types if needed
    if class_name == 'datetime':
        return datetime.datetime(**target)
    if class_name == 'StreamingBody':
        return BytesIO(target['body'])
    if class_name == 'CaseInsensitiveDict':
        return CaseInsensitiveDict(target['as_dict'])
    # Return unrecognized structures as-is
    return obj


def serialize_patch(obj):
    """Convert objects into JSON structures."""
    # Record class and module information for deserialization

    result = {'__class__': obj.__class__.__name__}
    try:
        result['__module__'] = obj.__module__
    except AttributeError:
        pass
    # Convert objects to dictionary representation based on type
    if isinstance(obj, datetime.datetime):
        result['year'] = obj.year
        result['month'] = obj.month
        result['day'] = obj.day
        result['hour'] = obj.hour
        result['minute'] = obj.minute
        result['second'] = obj.second
        result['microsecond'] = obj.microsecond
        return result
    if isinstance(obj, StreamingBody):
        original_text = obj.read()

        # We remove a BOM here if it exists so that it doesn't get reencoded
        # later on into a UTF-16 string, presumably by the json library
        result['body'] = original_text.decode('utf-8-sig')

        obj._raw_stream = BytesIO(original_text)
        obj._amount_read = 0
        return result
    if isinstance(obj, CaseInsensitiveDict):
        result['as_dict'] = dict(obj)
        return result
    raise TypeError('Type not serializable')
