#!/usr/bin/env python

# Helper for cloudformation

import troposphere
from pyhocon import ConfigFactory
from troposphere.cloudformation import AWSCustomObject
from tabulate import tabulate
import boto3
import sys
from clint.textui import colored, prompt, validators
import os
import time
from datetime import tzinfo, timedelta, datetime

# http://stackoverflow.com/questions/796008/cant-subtract-offset-naive-and-offset-aware-datetimes/25662061#25662061
ZERO = timedelta(0)


class UTC(tzinfo):
    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO


utc = UTC()


class StackLookup(object):
    """
    Class to handle stack lookups
    """

    PARAMETER_LOOKUP_PREFIX = 'CfOut_'

    def __init__(self, template, param_lambda_lookup_arn, param_stack_dependent_on):
        """
        Adds function to cloudformation template to lookup stack information
        :param template: The cloudformation template
        :param param_lambda_lookup_arn: The parameter stating the ARN of the COPS provided Lambda lookup function
        :param param_stack_dependent_on: The parameter stating the stack name which should be lookedup from
        """

        class CustomStackOutput(AWSCustomObject):
            resource_type = "Custom::StackOutput"

            props = {
                'ServiceToken': (basestring, True),
                'StackName': (basestring, True)
            }

        self.__custom_stack_obj = template.add_resource(CustomStackOutput(
            "StackOutput",
            ServiceToken=troposphere.Ref(
                param_lambda_lookup_arn
            ),
            StackName=troposphere.Ref(param_stack_dependent_on),
        ))

    def get_att(self, parameter):
        """
        Retrieves an attribute from an existing stack
        :param parameter: The output parameter which should be retrieved
        :return: Value of parameter to retrieve
        """

        # TODO fix concat prefix -> see support ticket
        return troposphere.GetAtt(
            self.__custom_stack_obj,
            # troposphere.Join(
            #     "",
            #     [
            #         self.PARAMETER_LOOKUP_PREFIX,
            troposphere.Ref(parameter)
            #     ]
            # )
        )


def json2table(json):
    filter_terms = ["ResponseMetadata"]
    table = []
    try:
        for k, v in filter(lambda (k, v): k not in filter_terms, json.iteritems()):
            table.append([k, str(v)])
        return tabulate(table, tablefmt="fancy_grid")
    except Exception as e:
        return json


def are_credentials_still_valid():
    client = boto3.client("lambda")
    try:
        client.list_functions()
    except Exception as e:
        print colored.red("Your credentials have expired... Please renew and try again!")
        sys.exit(1)
    else:
        pass


def read_kumo_config():
    homedir = os.path.expanduser('~')
    kumo_config_file = homedir + "/" + ".kumo"
    try:
        config = ConfigFactory.parse_file(kumo_config_file)
        return config
    except Exception as e:
        print e
        print colored.red("Cannot find file .kumo in your home directory %s" % kumo_config_file)
        print colored.red("Please run 'kumo configure'")
        sys.exit(1)


def get_input():
    name = prompt.query('Please enter your Slack API token: ')
    return name


def get_stack_id(stackName):
    client = boto3.client("cloudformation")
    response = client.describe_stacks(StackName=stackName)
    stack_id = response["Stacks"][0]["StackId"]
    return stack_id

def create_dp_name(env, layer, name):
    if env == "dev":
        return "dp-dev-" + layer + "-" + name
    elif env == "prod":
        return "dp-prod" + layer + "-" + name
    else:
        raise Exception("Unknown env: " + env)

def poll_stack_events(stackName):
    finished_statuses = ["CREATE_COMPLETE",
                         "CREATE_FAILED",
                         "DELETE_COMPLETE",
                         "DELETE_FAILED",
                         "ROLLBACK_COMPLETE",
                         "ROLLBACK_FAILED",
                         "UPDATE_COMPLETE",
                         "UPDATE_ROLLBACK_COMPLETE",
                         "UPDATE_ROLLBACK_FAILED"]

    failed_statuses = ["CREATE_FAILED",
                       "DELETE_FAILED",
                       "ROLLBACK_COMPLETE",
                       "ROLLBACK_FAILED",
                       "UPDATE_ROLLBACK_COMPLETE",
                       "UPDATE_ROLLBACK_FAILED"]

    warning_statuses = ["ROLLBACK_IN_PROGRESS",
                        "UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS",
                        "UPDATE_ROLLBACK_IN_PROGRESS"]

    success_statuses = ["CREATE_COMPLETE",
                        "DELETE_COMPLETE",
                        "UPDATE_COMPLETE"]

    seen_events = []
    # print len(seen_events)
    client = boto3.client("cloudformation")
    # the actual call to AWS has a little headstart
    now = datetime.now(utc) - timedelta(seconds=10)
    status = ""
    # for the delete command we need the stack_id
    stack_id = get_stack_id(stackName)

    while status not in finished_statuses:
        response = client.describe_stack_events(StackName=stack_id)
        for event in response["StackEvents"][::-1]:
            if event["EventId"] not in seen_events and event["Timestamp"] > now:
                seen_events.append(event["EventId"])
                resource_status = event["ResourceStatus"]
                resource_id = event["LogicalResourceId"]
                timestamp = str(event["Timestamp"])
                message = "%-25s %-50s %-25s\n" % (resource_status, resource_id, timestamp)
                if resource_status in failed_statuses:
                    print colored.red(message)
                elif resource_status in warning_statuses:
                    print colored.yellow(message)
                elif resource_status in success_statuses:
                    print colored.green(message)
                else:
                    print message
                if event["LogicalResourceId"] == stackName:
                    status = event["ResourceStatus"]
        time.sleep(5)
    exit_code = 0
    if status not in success_statuses:
        exit_code = 1
    return exit_code
