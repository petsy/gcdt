#!/usr/bin/env python

# from
# http://stackoverflow.com/questions/279237/import-a-module-from-a-relative-path
from __future__ import print_function

import os
import boto3
import sys
import random
import string
import utils

import monitoring

if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

import cloudformation

from docopt import docopt
from kumo_util import json2table, are_credentials_still_valid, read_kumo_config, get_input, poll_stack_events
from clint.textui import colored
from cookiecutter.main import cookiecutter
from glomex_utils.config_reader import read_config, get_env
from pyhocon.exceptions import ConfigMissingException


# TODO
# move slack

# creating docopt parameters and usage help
doc = """Usage:
        kumo deploy
        kumo list
        kumo delete -f
        kumo generate
        kumo validate
        kumo scaffold [<stackname>]
        kumo configure
        kumo preview
        kumo version

-h --help           show this

"""

KUMO_CONFIG = read_kumo_config()
CONFIG_KEY = "cloudformation"
SLACK_TOKEN = KUMO_CONFIG.get("kumo.slack-token")

boto_session = boto3.session.Session()


def call_pre_hook():
    if "pre_hook" in dir(cloudformation):
        print(colored.green("Executing pre hook..."))
        cloudformation.pre_hook()
    else:
        print("no pre hook found")


def call_pre_create_hook():
    if "pre_create_hook" in dir(cloudformation):
        print(colored.green("Executing pre create hook..."))
        cloudformation.pre_create_hook()
    else:
        print("no pre create hook found")


def call_pre_update_hook():
    if "pre_update_hook" in dir(cloudformation):
        print(colored.green("Executing pre update hook..."))
        cloudformation.pre_update_hook()
    else:
        print("no pre update hook found")


def call_post_create_hook():
    if "post_create_hook" in dir(cloudformation):
        print(colored.green("CloudFormation is done, now executing post create hook..."))
        cloudformation.post_create_hook()
    else:
        print("no post create hook found")


def call_post_update_hook():
    if "post_update_hook" in dir(cloudformation):
        print(colored.green("CloudFormation is done, now executing post update hook..."))
        cloudformation.post_update_hook()
    else:
        print("no post update hook found")


def call_post_hook():
    if "post_hook" in dir(cloudformation):
        print(colored.green("CloudFormation is done, now executing post  hook..."))
        cloudformation.post_hook()
    else:
        print("no post hook found")


# generate an entry for the parameter list from a raw value read from config
def generate_parameter_entry(conf, raw_param):
    entry = {
        'ParameterKey': raw_param,
        'ParameterValue': get_conf_value(conf, raw_param),
        'UsePreviousValue': False
    }
    return entry


def get_conf_value(conf, raw_param):
    conf_value = conf.get(CONFIG_KEY + "." + raw_param)
    if isinstance(conf_value, list):    # if list or array then join to comma seperated list
        return ",".join(conf_value)
    else:
        return conf_value


# generate the parameter list for the cloudformation template from the
# conf keys
def generate_parameters(conf):
    raw_parameters = []
    parameter_list = []
    for item in conf.iterkeys():
        for key in conf[item].iterkeys():
            if key not in ["StackName", "TemplateBody", "ArtifactBucket"]:
                raw_parameters.append(key)
    for param in raw_parameters:
        entry = generate_parameter_entry(conf, param)
        parameter_list.append(entry)

    return parameter_list


def stack_exists(stackName):
    client = boto_session.client('cloudformation')
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

def s3_upload(conf):
    region = boto_session.region_name
    resource_s3 = boto_session.resource('s3')
    bucket = get_artifact_bucket(conf)
    dest_key = "kumo/%s/%s-cloudformation.json" % (region, get_stack_name(conf))

    source_file = generate_template_file(conf)

    s3obj = resource_s3.Object(bucket, dest_key)
    s3obj.upload_file(source_file)
    s3obj.wait_until_exists()

    s3url = "https://s3-%s.amazonaws.com/%s/%s" % (region, bucket, dest_key)

    return s3url


def create_stack(conf):
    client_cf = boto_session.client('cloudformation')
    call_pre_create_hook()
    try:
        get_artifact_bucket(conf)
        response = client_cf.create_stack(
            StackName=get_stack_name(conf),
            TemplateURL=s3_upload(conf),
            Parameters=generate_parameters(conf),
            Capabilities=[
                'CAPABILITY_IAM',
            ],
        )
    except ConfigMissingException:
        response = client_cf.create_stack(
            StackName=get_stack_name(conf),
            TemplateBody=cloudformation.generate_template(),
            Parameters=generate_parameters(conf),
            Capabilities=[
                'CAPABILITY_IAM',
            ],
        )

    message = "kumo bot: created stack %s " % get_stack_name(conf)
    monitoring.slacker_notifcation("systemmessages", message, SLACK_TOKEN)
    stackname = get_stack_name(conf)
    exit_code = poll_stack_events(boto_session, stackname)
    call_post_create_hook()
    call_post_hook()
    sys.exit(exit_code)


# update stack with all the information we have

def update_stack(conf):
    client_cf = boto_session.client('cloudformation')
    try:
        call_pre_update_hook()
        try:
            get_artifact_bucket(conf)
            response = client_cf.update_stack(
                StackName=get_stack_name(conf),
                TemplateURL=s3_upload(conf),
                Parameters=generate_parameters(conf),
                Capabilities=[
                    'CAPABILITY_IAM',
                ],
            )
        except ConfigMissingException:
            response = client_cf.update_stack(
                StackName=get_stack_name(conf),
                TemplateBody=cloudformation.generate_template(),
                Parameters=generate_parameters(conf),
                Capabilities=[
                    'CAPABILITY_IAM',
                ],
            )

        message = "kumo bot: updated stack %s " % get_stack_name(conf)
        monitoring.slacker_notifcation("systemmessages", message, SLACK_TOKEN)
        stackname = get_stack_name(conf)
        exit_code = poll_stack_events(boto_session, stackname)
        call_post_update_hook()
        call_post_hook()
        sys.exit(exit_code)
    except Exception as e:
        if "No updates" in repr(e):
            print(colored.yellow("No updates are to be performed."))
        else:
            print(e)


# delete stack
def delete_stack(conf):
    client_cf = boto_session.client('cloudformation')
    response = client_cf.delete_stack(
        StackName=get_stack_name(conf),
    )
    message = "kumo bot: deleted stack %s " % get_stack_name(conf)
    monitoring.slacker_notifcation("systemmessages", message, SLACK_TOKEN)
    stackname = get_stack_name(conf)
    exit_code = poll_stack_events(boto_session, stackname)
    sys.exit(exit_code)


# validates the stack

# @make_spin(Default, "Validating stack...")
def validate_stack():
    client_cf = boto_session.client('cloudformation')
    template_body = cloudformation.generate_template()
    response = client_cf.validate_template(
        TemplateBody=template_body
    )
    print(json2table(response))


def list_stacks():
    client_cf = boto_session.client('cloudformation')
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
        print(json2table(result))
        stack_sum += 1
    print("listed %s stacks" % str(stack_sum))


def create_change_set(conf):
    client = boto_session.client('cloudformation')
    change_set_name = ''.join(random.SystemRandom().choice(
        string.ascii_uppercase + string.digits) for _ in range(8))
    response = client.create_change_set(
        StackName=get_stack_name(conf),
        TemplateBody=cloudformation.generate_template(),
        Parameters=generate_parameters(conf),
        Capabilities=[
            'CAPABILITY_IAM',
        ],
        ChangeSetName=change_set_name

    )
    # print json2table(response)
    return change_set_name, get_stack_name(conf)


def describe_change_set(change_set_name, stack_name):
    client = boto_session.client('cloudformation')

    completed = "CREATE_COMPLETE"
    status = ""
    while status != completed:
        response = client.describe_change_set(
            ChangeSetName=change_set_name,
            StackName=stack_name)
        status = response["Status"]
        if status == completed:
            for change in response["Changes"]:
                print(json2table(change["ResourceChange"]))


# writes the template to disk


# @make_spin(Default, "Generating template file...")
def generate_template_file(conf):
    template_body = cloudformation.generate_template()
    template_file_name = get_stack_name(conf) + "-generated-cf-template.json"
    with open(template_file_name, 'w') as opened_file:
        opened_file.write(template_body)
    print("wrote cf-template for {} to disk: {}".format(get_env(), template_file_name))
    return template_file_name


def get_stack_name(conf):
    return conf.get("cloudformation.StackName")


def get_artifact_bucket(conf):
    return conf.get("cloudformation.artifactBucket")


def scaffold():
    # Create project from the cookiecutter-pypackage/ template
    template_path = os.path.join(
        os.path.dirname(__file__), 'cookiecutter-kumo')
    cookiecutter(template_path)


def configure():
    homedir = os.path.expanduser('~')
    kumo_config_file = homedir + "/" + ".kumo"
    stack_name = get_input()
    with open(kumo_config_file, "w") as config:
        config.write("kumo {\n")
        config.write("slack-token=%s" % stack_name)
        config.write("\n}")


# very cool, but depends on having phantom.js installed
# leaving this for later
"""
def estimate_cost(conf):
    client = boto_session.client('cloudformation')
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
    arguments = docopt(doc)
    conf = None

    # Run command
    if arguments["deploy"]:
        call_pre_hook()
        conf = read_config()
        are_credentials_still_valid(boto_session)
        deploy_stack(conf)
    elif arguments["delete"]:
        conf = read_config()
        are_credentials_still_valid(boto_session)
        delete_stack(conf)
    elif arguments["validate"]:
        conf = read_config()
        are_credentials_still_valid(boto_session)
        validate_stack()
    elif arguments["generate"]:
        conf = read_config()
        generate_template_file(conf)
    elif arguments["list"]:
        are_credentials_still_valid(boto_session)
        list_stacks()
    elif arguments["scaffold"]:
        scaffold()
    elif arguments["configure"]:
        configure()
    elif arguments["preview"]:
        conf = read_config()
        are_credentials_still_valid(boto_session)
        change_set, stack_name = create_change_set(conf)
        describe_change_set(change_set, stack_name)
    elif arguments["version"]:
        utils.version()
        # elif arguments["costestimate"]:
        #     if os.getcwd() not in sys.path:
        #         sys.path.insert(0, os.getcwd())
        #     conf = read_config()
        #     import cloudformation
        #     are_credentials_still_valid(boto_session)
        #     estimate_cost(conf)


if __name__ == '__main__':
    main()
