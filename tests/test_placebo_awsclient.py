# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import os

import pytest
import botocore

from . import here
from .placebo_awsclient import PlaceboAWSClient


@pytest.fixture(scope='function')  # 'function' or 'module'
def awsclient(request):
    # note this is a specialized version since the version in helpers_aws is
    # controlled via env variables
    prefix = request.module.__name__ + '.' + request.function.__name__
    record_dir = os.path.join(here('./resources/placebo_awsclient'), prefix)

    with PlaceboAWSClient(botocore.session.Session(), data_path=record_dir) as client:
        #client.record()  # switch record mode
        #client.playback()  # switch playback mode
        #client.add_response('list_objects', response, expected_params)
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


# I do not think we need the bookkeeping!
#def test_clients(self):
#    ec2 = self.session.client('ec2')
#    iam = self.session.client('iam')
#    assert len(awsclient.clients), 2)
#    self.assertTrue(ec2 in awsclient.clients)
#    self.assertTrue(iam in awsclient.clients)
#    session = boto3.Session(profile_name='foobar',
#                            region_name='us-west-2')
#    new_ec2 = session.client('ec2')
#    assert len(awsclient.clients), 2)
#    self.assertFalse(new_ec2 in awsclient.clients)


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
