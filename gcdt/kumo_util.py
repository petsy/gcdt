# -*- coding: utf-8 -*-

"""The kumo_util file contains stuff that is used for example in cloudformation.py
templates or from other external code.
"""

from __future__ import print_function

import troposphere
from troposphere.cloudformation import AWSCustomObject


class StackLookup(object):
    """Class to handle stack lookups
    """

    def __init__(self, template, param_lambda_lookup_arn,
                 param_stack_dependent_on=None):
        """Adds function to cloudformation template to lookup stack information
        :param template: The cloudformation template
        :param param_lambda_lookup_arn: The parameter stating the ARN of the
            COPS provided Lambda lookup function
        :param param_stack_dependent_on: The parameter stating the stack name
            which should be lookedup from (Default: None)
        """
        if param_stack_dependent_on is not None:
            class CustomStackOutput(AWSCustomObject):
                resource_type = 'Custom::StackOutput'

                props = {
                    'ServiceToken': (basestring, True),
                    'StackName': (basestring, True)
                }

            self.__custom_stack_obj = template.add_resource(CustomStackOutput(
                'StackOutput',
                ServiceToken=troposphere.Ref(
                    param_lambda_lookup_arn
                ),
                StackName=troposphere.Ref(param_stack_dependent_on),
            ))
        else:
            class CustomStackOutput(AWSCustomObject):
                resource_type = 'Custom::StackOutput'

                props = {
                    'ServiceToken': (basestring, True)
                }

            self.__custom_stack_obj = template.add_resource(CustomStackOutput(
                'StackOutput',
                ServiceToken=troposphere.Ref(
                    param_lambda_lookup_arn
                ),
            ))

    def get_att(self, parameter, as_reference=True):
        """Retrieves an attribute from an existing stack
        :param parameter: The output parameter which should be retrieved
        :param as_reference: Is the parameter a reference (Default) or a string
        :return: Value of parameter to retrieve
        """
        if as_reference:
            return troposphere.GetAtt(
                self.__custom_stack_obj,
                troposphere.Ref(parameter)
            )
        else:
            return troposphere.GetAtt(
                self.__custom_stack_obj,
                parameter
            )


def ensure_ebs_volume_tags_autoscaling_group(boto_session, as_group_name, tags):
    # I think this is only relevant to test code!
    ec2_client = boto_session.client('ec2')

    autoscale_filter = {
        'Name': 'tag:aws:autoscaling:groupName',
        'Values': [as_group_name]
    }
    response = ec2_client.describe_instances(Filters=[autoscale_filter])
    for r in response['Reservations']:
        for i in r['Instances']:
            ensure_ebs_volume_tags_ec2_instance(boto_session, i['InstanceId'],
                                                tags)


def ensure_ebs_volume_tags_ec2_instance(boto_session, instance_id, tags):
    # I think this is only relevant to test code!
    ec2_resource = boto_session.resource('ec2')
    instance  = ec2_resource.Instance(instance_id)
    for vol in instance.volumes.all():
        ensure_tags_ebs_volume(vol, tags)


def ensure_tags_ebs_volume(volume, tags):
    # I think this is only relevant to test code!
    tags_to_add = []
    if volume.tags:
        for tag in tags:
            if not tag in volume.tags:
                tags_to_add.append(tag)
        if tags_to_add:
            volume.create_tags(Tags = tags_to_add)
    else:
        volume.create_tags(Tags = tags)
