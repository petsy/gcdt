# -*- coding: utf-8 -*-
from __future__ import print_function
from distutils.version import StrictVersion
from datetime import tzinfo, timedelta, datetime
import locale
import re
#import boto3


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

    locale.setlocale(locale.LC_ALL, 'C')
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
    client_cf = awsclient.get_client('cloudformation')
    response = client_cf.describe_stacks(StackName=stack_name)
    result = {}
    for output in response["Stacks"][0]["Outputs"]:
        result[output["OutputKey"]] = output["OutputValue"]
    return result


def get_ssl_certificate(awsclient, domain):
    client_iam = awsclient.get_client('iam')
    response = client_iam.list_server_certificates()
    arn = ""
    for cert in response["ServerCertificateMetadataList"]:
        if domain in cert["ServerCertificateName"]:
            if datetime.now(UTC()) > cert['Expiration']:
                print("certificate has expired")
            else:
                arn = cert["Arn"]
                break
    return arn


def get_base_ami(awsclient):
    """
    return the latest version of our base AMI
    we can't use tags for this, so we have only the name as resource
    """
    #client_ec2 = awsclient.resource('ec2')
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
    #for i in client_ec2.images.filter(Owners=['569909643510'],
    # TODO hardcoded account_id, really?
    for i in client_ec2.describe_images(
            Owners=['569909643510'],
            Filters=image_filter
            ):
        m = re.search(r'(Ops_Base-Image)_(\d+.\d+.\d+)_(\d+)$', i.name)
        if m:
            version = StrictVersion(m.group(2))
            timestamp = m.group(3)
            creation_date = parse_ts(i.creation_date)

            if creation_date > latest_ts and version >=latest_version:
                latest_id = i.id
                latest_ts = creation_date
                latest_version = version

    return latest_id
