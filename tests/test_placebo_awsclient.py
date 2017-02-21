# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import os
import datetime
import json

import pytest
import botocore.session

from .placebo_awsclient import PlaceboAWSClient, serialize_patch, deserialize, \
    UTC
from .helpers import temp_folder  # fixture!
from . import here


@pytest.fixture(scope='function')  # 'function' or 'module'
def awsclient(request, temp_folder):
    # note this is a specialized version since the version in helpers_aws is
    # controlled via env variables
    prefix = request.module.__name__ + '.' + request.function.__name__
    record_dir = os.path.join(temp_folder[0], 'placebo_awsclient', prefix)
    if not os.path.exists(record_dir):
        os.makedirs(record_dir)

    client = PlaceboAWSClient(botocore.session.Session(), data_path=record_dir)
    yield client


### from test_pill.py
def test_record(awsclient):
    assert awsclient._mode is None
    awsclient.record()
    assert awsclient._mode == 'record'
    assert awsclient._events == ['after-call.*.*']
    awsclient.stop()
    assert awsclient._mode is None
    assert awsclient._events == []
    awsclient.record('ec2')
    awsclient.record('iam', 'ListUsers')
    assert awsclient._mode, 'record'
    assert awsclient._events == ['after-call.ec2.*', 'after-call.iam.ListUsers']
    awsclient.stop()
    assert awsclient._mode is None
    assert awsclient._events == []


def test_playback(awsclient):
    awsclient.playback()
    assert awsclient._mode == 'playback'
    assert awsclient._events == ['before-call.*.*']
    awsclient.stop()
    assert awsclient._events == []


### from test_save.py
kp_result_one = {
    "KeyPairs": [
        {
            "KeyName": "foo",
            "KeyFingerprint": "ad:08:8a:b3:13:ea:6c:20:fa"
        }
    ]
}

kp_result_two = {
    "KeyPairs": [
        {
            "KeyName": "bar",
            "KeyFingerprint": ":27:21:b9:ce:b5:5a:a2:a3:bc"
        }
    ]
}

addresses_result_one = {
    "Addresses": [
        {
            "InstanceId": "",
            "PublicIp": "192.168.0.1",
            "Domain": "standard"
        }
    ]
}


def test_ec2(awsclient):
    assert len(os.listdir(awsclient._data_path)) == 0
    awsclient._save_response(
        'ec2', 'DescribeAddresses', addresses_result_one)
    assert len(os.listdir(awsclient._data_path)) == 1

    awsclient.playback()
    ec2_client = awsclient.get_client('ec2')
    result = ec2_client.describe_addresses()
    assert result['Addresses'][0]['PublicIp'] == '192.168.0.1'
    result = ec2_client.describe_addresses()
    assert result['Addresses'][0]['PublicIp'] == '192.168.0.1'


def test_ec2_multiple_responses(awsclient):
    assert len(os.listdir(awsclient._data_path)) == 0
    awsclient._save_response(
        'ec2', 'DescribeKeyPairs', kp_result_one)
    assert len(os.listdir(awsclient._data_path)) == 1
    awsclient._save_response(
        'ec2', 'DescribeKeyPairs', kp_result_two)
    assert len(os.listdir(awsclient._data_path)) == 2

    awsclient.playback()
    ec2_client = awsclient.get_client('ec2')
    result = ec2_client.describe_key_pairs()
    assert result['KeyPairs'][0]['KeyName'] == 'foo'
    result = ec2_client.describe_key_pairs()
    assert result['KeyPairs'][0]['KeyName'] == 'bar'
    result = ec2_client.describe_key_pairs()
    assert result['KeyPairs'][0]['KeyName'] == 'foo'


def test_multiple_clients(awsclient):
    assert len(os.listdir(awsclient._data_path)) == 0
    awsclient._save_response(
        'ec2', 'DescribeAddresses', addresses_result_one)

    awsclient.playback()
    ec2_client = awsclient.get_client('ec2')
    iam_client = awsclient.get_client('iam')
    result = ec2_client.describe_addresses()
    assert len(os.listdir(awsclient._data_path)) == 1


### from test_canned.py
def test_describe_addresses(awsclient):
    awsclient._data_path = here('./resources/placebo_awsclient_canned')
    awsclient.playback()
    ec2_client = awsclient.get_client('ec2')
    result = ec2_client.describe_addresses()
    assert result['Addresses'][0]['PublicIp'] == '52.53.54.55'
    result = ec2_client.describe_addresses()
    assert result['Addresses'][0]['PublicIp'] == '53.54.55.56'
    result = ec2_client.describe_addresses()
    assert result['Addresses'][0]['PublicIp'] == '52.53.54.55'
    result = ec2_client.describe_addresses()
    assert result['Addresses'][0]['PublicIp'] == '53.54.55.56'


def test_describe_key_pairs(awsclient):
    awsclient._data_path = here('./resources/placebo_awsclient_canned')
    awsclient.playback()
    ec2_client = awsclient.get_client('ec2')
    result = ec2_client.describe_key_pairs()
    assert len(result['KeyPairs']) == 2
    assert result['KeyPairs'][0]['KeyName'] == 'FooBar'
    assert result['KeyPairs'][1]['KeyName'] == 'FieBaz'


def test_prefix_new_file_path(awsclient):
    awsclient._data_path = here('./resources/placebo_awsclient_canned')
    service = 'foo'
    operation = 'DescribeAddresses'
    filename = '{0}.{1}_2.json'.format(service, operation)
    target = os.path.join(awsclient._data_path, filename)
    assert awsclient._get_new_file_path(service, operation) == target


def test_prefix_next_file_path(awsclient):
    awsclient._data_path = here('./resources/placebo_awsclient_canned')
    service = 'foo'
    operation = 'DescribeAddresses'
    filename = '{0}.{1}_1.json'.format(service, operation)
    target = os.path.join(awsclient._data_path, filename)
    assert awsclient._get_next_file_path(service, operation) == target


### from test_serializers.py
date_sample = {
    "LoginProfile": {
        "UserName": "baz",
        "CreateDate": datetime.datetime(2015, 1, 4, 9, 1, 2, 0, tzinfo=UTC()),
    }
}

date_json = """{"LoginProfile": {"CreateDate": {"__class__": "datetime", "day": 4, "hour": 9, "microsecond": 0, "minute": 1, "month": 1, "second": 2, "year": 2015}, "UserName": "baz"}}"""


def test_serialize_datetime_to_json():
    result = json.dumps(date_sample, default=serialize_patch, sort_keys=True)
    assert result == date_json


def test_deserialize_datetime_from_json():
    response = json.loads(date_json, object_hook=deserialize)
    assert response == date_sample
