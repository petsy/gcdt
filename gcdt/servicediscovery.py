# -*- coding: utf-8 -*-
"""
Note: This is used in cloudformation templates (at least in parts)
A refactoring might break team-code!!
"""
from __future__ import unicode_literals, print_function
from distutils.version import StrictVersion
from datetime import tzinfo, timedelta, datetime
import re


ZERO = timedelta(0)


class UTC(tzinfo):
    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO


def parse_ts(ts):
    ISO8601 = '%Y-%m-%dT%H:%M:%SZ'
    ISO8601_MS = '%Y-%m-%dT%H:%M:%S.%fZ'
    RFC1123 = '%a, %d %b %Y %H:%M:%S %Z'

    # commented out after discussion with Andy 08.03.2017
    #locale.setlocale(locale.LC_ALL, 'C')
    ts = ts.strip()
    try:
        dt = datetime.strptime(ts, ISO8601)
        return dt
    except ValueError:
        try:
            dt = datetime.strptime(ts, ISO8601_MS)
            return dt
        except ValueError:
            dt = datetime.strptime(ts, RFC1123)
            return dt


# gets Outputs for a given StackName
def get_outputs_for_stack(awsclient, stack_name):
    """
    Read environment from ENV and mangle it to a (lower case) representation
    Note: gcdt.servicediscovery get_outputs_for_stack((awsclient, stack_name)
    is used in many cloudformation.py templates!

    :param awsclient:
    :param stack_name:
    :return: dictionary containing the stack outputs
    """
    client_cf = awsclient.get_client('cloudformation')
    response = client_cf.describe_stacks(StackName=stack_name)
    if response['Stacks'] and 'Outputs' in response['Stacks'][0]:
        result = {}
        for output in response['Stacks'][0]['Outputs']:
            result[output['OutputKey']] = output['OutputValue']
        return result


def get_ssl_certificate(awsclient, domain):
    client_iam = awsclient.get_client('iam')
    response = client_iam.list_server_certificates()
    arn = ""
    for cert in response["ServerCertificateMetadataList"]:
        if domain in cert["ServerCertificateName"]:
            print(cert['Expiration'])
            print(datetime.now(UTC()))
            if datetime.now(UTC()) > cert['Expiration']:
                print("certificate has expired")
            else:
                arn = cert["Arn"]
                break
    return arn


def get_base_ami(awsclient, owners):
    """
    return the latest version of our base AMI
    we can't use tags for this, so we have only the name as resource
    """
    client_ec2 = awsclient.get_client('ec2')
    image_filter = [
        {
            'Name': 'state',
            'Values': [
                'available',
            ]
        },
    ]

    latest_ts = datetime.fromtimestamp(0)
    latest_version = StrictVersion('0.0.0')
    latest_id = None
    for i in client_ec2.describe_images(
            Owners=owners,
            Filters=image_filter
            )['Images']:
        m = re.search(r'(Ops_Base-Image)_(\d+.\d+.\d+)_(\d+)$', i['Name'])
        if m:
            version = StrictVersion(m.group(2))
            timestamp = m.group(3)
            creation_date = parse_ts(i['CreationDate'])

            if creation_date > latest_ts and version >=latest_version:
                latest_id = i['ImageId']
                latest_ts = creation_date
                latest_version = version

    return latest_id
