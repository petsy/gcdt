# -*- coding: utf-8 -*-

"""Helper to create Route53 entries
"""

# TODO: this is probably only used in cloudformation
# TODO: add documentation how to use it!

from __future__ import unicode_literals, print_function
import sys

import troposphere
from troposphere.ec2 import Instance
from troposphere.route53 import RecordSetType

from .utils import get_env
from .servicediscovery import get_outputs_for_stack

TTL_DEFAULT = 300
HOST_ZONE_NAME__STACK_OUTPUT_NAME = "internalDomainName"
_host_zone_name = None


def create_record(awsclient, name_prefix, instance_reference, type="A", host_zone_name=None):
    """
    Builds route53 record entries enabling DNS names for services
    Note: gcdt.route53 create_record(awsclient, ...)
    is used in dataplatform cloudformation.py templates!

    :param name_prefix: The sub domain prefix to use
    :param instance_reference: The EC2 troposphere reference which's private IP should be linked to
    :param type: The type of the record  A or CNAME (default: A)
    :param host_zone_name: The host zone name to use (like preprod.ds.glomex.cloud. - DO NOT FORGET THE DOT!)
    :return: RecordSetType
    """

    # Only fetch the host zone from the COPS stack if nessary
    if host_zone_name is None:
        host_zone_name = _retrieve_stack_host_zone_name(awsclient)

    if not (type == "A" or type == "CNAME"):
        raise Exception("Record set type is not supported!")

    name_of_record = name_prefix \
                         .replace('.', '') \
                         .replace('-', '') \
                         .title() + "HostRecord"

    # Reference EC2 instance automatically to their private IP
    if isinstance(instance_reference, Instance):
        resource_record = troposphere.GetAtt(
                instance_reference,
                "PrivateIp"
        )
    else:
        resource_record = instance_reference

    return RecordSetType(
            name_of_record,
            HostedZoneName=host_zone_name,
            Name=troposphere.Join("", [
                name_prefix + ".",
                host_zone_name,
            ]),
            Type=type,
            TTL=TTL_DEFAULT,
            ResourceRecords=[
                resource_record
            ],
    )


def _retrieve_stack_host_zone_name(awsclient, default_stack_name=None):
    """
    Use service discovery to get the host zone name from the default stack

    :return: Host zone name as string
    """
    global _host_zone_name

    if _host_zone_name is not None:
        return _host_zone_name

    env = get_env()

    if env is None:
        print("Please set environment...")
        # TODO: why is there a sys.exit in library code used by cloudformation!!!
        sys.exit()

    if default_stack_name is None:
        # TODO why 'dp-<env>'? - this should not be hardcoded!
        default_stack_name = 'dp-%s' % env
    default_stack_output = get_outputs_for_stack(awsclient, default_stack_name)

    if HOST_ZONE_NAME__STACK_OUTPUT_NAME not in default_stack_output:
        print("Please debug why default stack '{}' does not contain '{}'...".format(
                default_stack_name,
                HOST_ZONE_NAME__STACK_OUTPUT_NAME,
        ))
        # TODO: why is there a sys.exit in library code used by cloudformation!!!
        sys.exit()

    _host_zone_name = default_stack_output[HOST_ZONE_NAME__STACK_OUTPUT_NAME] + "."
    return _host_zone_name
