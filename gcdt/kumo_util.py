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


def create_dp_name(env, layer, name):
    """Deprecated! Please move this to dp_helper!

    :param env:
    :param layer:
    :param name:
    :return:
    """
    #TODO: lower() should be used on whole name!
    return 'dp-' + env.lower() + '-' + layer + '-' + name
