#!/usr/bin/env python

# from
# http://stackoverflow.com/questions/279237/import-a-module-from-a-relative-path
import os
import sys

import boto3
from docopt import docopt
from gcdt.config_reader import read_config
from gcdt import monitoring
import json
from tabulate import tabulate
import sys
from kumo_util import json2table, are_credentials_still_valid, read_kumo_config, get_input, poll_stack_events
from clint.textui import colored
import uuid
from cookiecutter.main import cookiecutter
#from selenium import webdriver
import random
import string

from pyspin.spin import make_spin, Default
import time

# TODO
# check credentials
# move config_reader
# move slack
# poll cloudformation for events
# move iam stuff to utils
# multi tenancy


# creating docopt parameters and usage help
doc = """Usage:
        kumo deploy [-e ENV]
        kumo list
        kumo delete -f [-e ENV]
        kumo generate [-e ENV]
        kumo validate [-e ENV]
        kumo scaffold [<stackname>]
        kumo configure
        kumo preview

-e ENV --env ENV    environment to use [default: dev] else is prod
-h --help           show this

"""

CONFIG_KEY = "cloudformation"


# generate an entry for the parameter list from a raw value read from config
def generate_parameter_entry(conf, raw_param):
    entry = {
        'ParameterKey': raw_param,
        'ParameterValue': conf.get(CONFIG_KEY + "." + raw_param),
        'UsePreviousValue': False
    }
    return entry


# generate the parameter list for the cloudformation template from the
# conf keys
def generate_parameters(conf):
    raw_parameters = []
    parameter_list = []
    for item in conf.iterkeys():
        for key in conf[item].iterkeys():
            if key not in ["StackName", "TemplateBody"]:
                raw_parameters.append(key)
    for param in raw_parameters:
        entry = generate_parameter_entry(conf, param)
        parameter_list.append(entry)

    # Print parameters
    # print "\n" + tabulate(
    #    parameter_list,
    #    headers='keys'
    # )

    return parameter_list


def stack_exists(stackName):
    client = boto3.client('cloudformation')
    try:
        response = client.describe_stacks(
            StackName=stackName
        )
    except Exception as e:
        return False
    else:
        return True


def deploy_stack(conf):
    stackname = get_stack_name(conf)
    if stack_exists(stackname):
        update_stack(conf)
    else:
        create_stack(conf)

# create stack with all the information we have

# @monitoring.event("cloudformation_deploy_tool", "DEPLOY - creating ")
# @make_spin(Default, "Creating stack...")
def create_stack(conf):
    client_cf = boto3.client('cloudformation')
    response = client_cf.create_stack(
        StackName=get_stack_name(conf),
        TemplateBody=cloudformation.generate_template(),
        Parameters=generate_parameters(conf),
        Capabilities=[
            'CAPABILITY_IAM',
        ],
    )
    message = "kumo bot: created stack %s " % get_stack_name(conf)
    #monitoring.slacker_notifcation("systemmessages", message)
    stackname = get_stack_name(conf)
    exit_code = poll_stack_events(stackname)
    sys.exit(exit_code)



# update stack with all the information we have

# @monitoring.event("cloudformation_deploy_tool", "DEPLOY - updating")
# @make_spin(Default, "Updating stack...")
def update_stack(conf):
    client_cf = boto3.client('cloudformation')
    try:
        response = client_cf.update_stack(
            StackName=get_stack_name(conf),
            TemplateBody=cloudformation.generate_template(),
            Parameters=generate_parameters(conf),
            Capabilities=[
                'CAPABILITY_IAM',
            ],
        )
        message = "kumo bot: updated stack %s " % get_stack_name(conf)
        #monitoring.slacker_notifcation("systemmessages", message)
        stackname = get_stack_name(conf)
        exit_code = poll_stack_events(stackname)
        sys.exit(exit_code)
    except Exception as e:
        print colored.yellow("No updates are to be performed.")


# delete stack
def delete_stack(conf):
    client_cf = boto3.client('cloudformation')
    response = client_cf.delete_stack(
        StackName=get_stack_name(conf),
    )
    message = "kumo bot: deleted stack %s " % get_stack_name(conf)
    #monitoring.slacker_notifcation("systemmessages", message)
    stackname = get_stack_name(conf)
    exit_code = poll_stack_events(stackname)
    sys.exit(exit_code)


# validates the stack

# @make_spin(Default, "Validating stack...")
def validate_stack():
    client_cf = boto3.client('cloudformation')
    template_body = cloudformation.generate_template()
    response = client_cf.validate_template(
        TemplateBody=template_body
    )
    print json2table(response)


def list_stacks():
    client_cf = boto3.client('cloudformation')
    response = client_cf.list_stacks(
        StackStatusFilter=[
            'CREATE_IN_PROGRESS', 'CREATE_COMPLETE', 'ROLLBACK_IN_PROGRESS', 'ROLLBACK_COMPLETE', 'DELETE_IN_PROGRESS',
            'DELETE_FAILED', 'UPDATE_IN_PROGRESS', 'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS', 'UPDATE_COMPLETE',
            'UPDATE_ROLLBACK_IN_PROGRESS', 'UPDATE_ROLLBACK_FAILED', 'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS',
            'UPDATE_ROLLBACK_COMPLETE',
        ]
    )
    result = {}
    stack_sum = 0
    for summary in response["StackSummaries"]:
        result["StackName"] = summary["StackName"]
        result["CreationTime"] = summary["CreationTime"]
        result["StackStatus"] = summary["StackStatus"]
        print json2table(result)
        stack_sum += 1
    print "listed %s stacks" % str(stack_sum)


def create_change_set(conf):
    client = boto3.client('cloudformation')
    change_set_name = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(8))
    response = client.create_change_set(
        StackName=get_stack_name(conf),
        TemplateBody=cloudformation.generate_template(),
        Parameters=generate_parameters(conf),
        Capabilities=[
            'CAPABILITY_IAM',
        ],
        ChangeSetName=change_set_name

    )
    #print json2table(response)
    return change_set_name, get_stack_name(conf)

def describe_change_set(change_set_name, stack_name):
    client = boto3.client('cloudformation')

    completed = "CREATE_COMPLETE"
    status = ""
    while status != completed:
        response = client.describe_change_set(
            ChangeSetName=change_set_name,
            StackName=stack_name)
        status = response["Status"]
        if status == completed:
            for change in response["Changes"]:
                print json2table(change["ResourceChange"])





# writes the template to disk


# @make_spin(Default, "Generating template file...")
def generate_template_file(conf):
    template_body = cloudformation.generate_template()
    template_file_name = get_stack_name(conf) + "-generated-cf-template.json"
    with open(template_file_name, 'w') as opened_file:
        opened_file.write(template_body)
    print("wrote cf-template for " + os.environ.get('ENV') +
          " to disk: %s") % (template_file_name)


def get_stack_name(conf):
    print conf
    return conf.get("cloudformation.StackName")


def config_from_file(env):
    os.environ['ENV'] = env

    # read config from given name
    return read_config()


def scaffold():
    # Create project from the cookiecutter-pypackage/ template
    template_path = os.path.join(os.path.dirname(__file__), 'cookiecutter-kumo')
    cookiecutter(template_path)


def configure():
    homedir = os.path.expanduser('~')
    kumo_config_file = homedir + "/" + ".kumo"
    stack_name = get_input()
    with open(kumo_config_file, "w") as config:
        config.write("kumo {\n")
        config.write("slack-token=%s" % stack_name)
        config.write("\n}")

def get_config(arguments):
    if arguments['--env'] == 'prod':
        conf = config_from_file('PROD')
    else:
        conf = config_from_file('DEV')

    return conf


# very cool, but depends on having phantom.js installed
# leaving this for later
"""
def estimate_cost(conf):
    client = boto3.client('cloudformation')
    response = client.estimate_template_cost(
        TemplateBody=cloudformation.generate_template(),
        Parameters=generate_parameters(conf),
    )
    url = response["Url"]
    driver = webdriver.PhantomJS()
    driver.set_window_size(1120, 550)
    driver.get(url)
    time.sleep(5)
    print driver.find_elements_by_class_name("billLabel")[0].text
    driver.quit()
"""

def main():
    global cloudformation
    arguments = docopt(doc)
    conf = None

    # Run command
    if arguments["deploy"]:
        env = (arguments["--env"] if arguments["--env"] else "DEV")
        if os.getcwd() not in sys.path:
            sys.path.insert(0, os.getcwd())
        conf = get_config(arguments)
        import cloudformation
        kumo_config = read_kumo_config()
        are_credentials_still_valid()
        print("deploy stack for " + os.environ.get('ENV') +
              ": " + get_stack_name(conf))
        deploy_stack(conf)
    elif arguments["delete"]:
        env = (arguments["--env"] if arguments["--env"] else "DEV")
        if os.getcwd() not in sys.path:
            sys.path.insert(0, os.getcwd())
        conf = get_config(arguments)
        import cloudformation
        kumo_config = read_kumo_config()
        are_credentials_still_valid()
        print("deleting stack for " + os.environ.get('ENV') +
              ": " + get_stack_name(conf))
        delete_stack(conf)
    elif arguments["validate"]:
        if os.getcwd() not in sys.path:
            sys.path.insert(0, os.getcwd())
        conf = get_config(arguments)
        import cloudformation
        kumo_config = read_kumo_config()
        are_credentials_still_valid()
        validate_stack()
    elif arguments["generate"]:
        if os.getcwd() not in sys.path:
            sys.path.insert(0, os.getcwd())
        conf = get_config(arguments)
        import cloudformation
        generate_template_file(conf)
    elif arguments["list"]:
        are_credentials_still_valid()
        list_stacks()
    elif arguments["scaffold"]:
        scaffold()
    elif arguments["configure"]:
        configure()
    elif arguments["preview"]:
        if os.getcwd() not in sys.path:
            sys.path.insert(0, os.getcwd())
        conf = get_config(arguments)
        import cloudformation
        kumo_config = read_kumo_config()
        are_credentials_still_valid()
        change_set, stack_name = create_change_set(conf)
        describe_change_set(change_set, stack_name)

    """
    elif arguments["costestimate"]:
        if os.getcwd() not in sys.path:
            sys.path.insert(0, os.getcwd())
        import cloudformation
        conf = get_config(arguments)
        kumo_config = read_kumo_config()
        are_credentials_still_valid()
        estimate_cost(conf)
    """

if __name__ == '__main__':
    main()