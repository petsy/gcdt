#!/usr/bin/env python
#
# Helper to create Route53 entries

import troposphere
from troposphere.route53 import RecordSetType
from glomex_utils.config_reader import get_env

HOST_ZONE_BASE_NAME = ".dp.glomex.cloud."
TTL_DEFAULT = 300


def create_record(name_prefix, instance_reference, type="A"):
    """
    Builds route53 record entries enabling DNS names for services

    :param name_prefix: The sub domain prefix to use
    :param instance_reference: The EC2 troposphere reference which's private IP should be linked to
    :param type: The type of the record  A or CNAME (default: A)
    :return: RecordSetType
    """
    if not (type == "A" or type == "CNAME"):
        raise Exception("Record set type is not supported!")

    name_of_record = name_prefix \
        .replace('.', '') \
        .replace('-', '') \
        .title() + "HostRecord"
    host_name_suffix = get_env() + HOST_ZONE_BASE_NAME

    return RecordSetType(
        name_of_record,
        HostedZoneName=host_name_suffix,
        Name=troposphere.Join("", [
            name_prefix + ".",
            host_name_suffix,
        ]),
        Type=type,
        TTL=TTL_DEFAULT,
        ResourceRecords=[
            troposphere.GetAtt(
                instance_reference,
                "PrivateIp"
            )
        ],
    )
