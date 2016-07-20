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
import json
import time
import pyhocon.exceptions
import monitoring
from tabulate import tabulate
from pyspin.spin import Default, Spinner
from docopt import docopt
from kumo_util import json2table, are_credentials_still_valid, read_kumo_config, get_input, poll_stack_events
from clint.textui import colored
from cookiecutter.main import cookiecutter
from glomex_utils.config_reader import read_config, get_env
from pyhocon.exceptions import ConfigMissingException

if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

CLOUDFORMATION_FOUND = True

try:
    import cloudformation
    #print ("using the following CloudFormation template: {}".format(cloudformation.__file__))
    template_directory=(os.path.dirname(cloudformation.__file__))
    cwd = (os.getcwd())

    if not template_directory == cwd:
        print(colored.red("FATAL: cloudformation.py imported outside of your current working directory" + template_directory +" Bailing out... "))
        sys.exit(1)
except ImportError:
    CLOUDFORMATION_FOUND = False
except Exception as e:
    print ("could not import cloudformation.py, maybe something wrong with your code?")
    print (e)
    CLOUDFORMATION_FOUND = False

# creating docopt parameters and usage help
doc = """Usage:
        kumo deploy [--override-stack-policy]
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

def print_parameter_diff(config):
    """
    print differences between local config and currently active config
    """
    cf = boto_session.resource('cloudformation')
    try:
        stackname = config['cloudformation.StackName']
        stack = cf.Stack(stackname)
    except pyhocon.exceptions.ConfigMissingException:
        print("StackName is not configured, could not create parameter diff")
        return None
    except:
        # probably the stack is not existing
        return None

    changed = 0
    table = []
    table.append(["Parameter", "Current Value", "New Value"])

    for param in stack.parameters:
        try:
            old = param['ParameterValue']
            new = config.get('cloudformation.' + param['ParameterKey'])
            if old != new:
                table.append([param['ParameterKey'], old, new])
                changed += 1
        except pyhocon.exceptions.ConfigMissingException:
            print('Did not find %s in local config file' % param['ParameterKey'])

    if changed > 0:
        print (tabulate(table, tablefmt="fancy_grid"))
        print(colored.red("Parameters have changed. Waiting 10 seconds. \n"))
        print("If parameters are unexpected you might want to exit now: control-c")
        # Choose a spin style.
        spin = Spinner(Default)
        # Spin it now.
        for i in range(100):
            print(u"\r{0}".format(spin.next()), end="")
            sys.stdout.flush()
            time.sleep(0.1)
        print("\n")



def call_pre_hook():
    if "pre_hook" in dir(cloudformation):
        print(colored.green("Executing pre hook..."))
        cloudformation.pre_hook()


def call_pre_create_hook():
    if "pre_create_hook" in dir(cloudformation):
        print(colored.green("Executing pre create hook..."))
        cloudformation.pre_create_hook()


def call_pre_update_hook():
    if "pre_update_hook" in dir(cloudformation):
        print(colored.green("Executing pre update hook..."))
        cloudformation.pre_update_hook()


def call_post_create_hook():
    if "post_create_hook" in dir(cloudformation):
        print(colored.green("CloudFormation is done, now executing post create hook..."))
        cloudformation.post_create_hook()


def call_post_update_hook():
    if "post_update_hook" in dir(cloudformation):
        print(colored.green("CloudFormation is done, now executing post update hook..."))
        cloudformation.post_update_hook()

# FIXME does not get called when no changes from CF to apply
def call_post_hook():
    if "post_hook" in dir(cloudformation):
        print(colored.green("CloudFormation is done, now executing post  hook..."))
        cloudformation.post_hook()


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


def deploy_stack(conf, override_stack_policy=False):
    stackname = get_stack_name(conf)
    if stack_exists(stackname):
        update_stack(conf, override_stack_policy)
    else:
        create_stack(conf, override_stack_policy)


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


def _get_stack_policy():
    default_stack_policy = json.dumps({
          "Statement" : [
            {
              "Effect" : "Allow",
              "Action" : "Update:Modify",
              "Principal": "*",
              "Resource" : "*"
            },
            {
              "Effect" : "Deny",
              "Action" : ["Update:Replace", "Update:Delete"],
              "Principal": "*",
              "Resource" : "*"
            }
          ]
        })

    stack_policy = default_stack_policy

    # check if a user specified his own stack policy
    if CLOUDFORMATION_FOUND:
        if "get_stack_policy" in dir(cloudformation):
            stack_policy = cloudformation.get_stack_policy()
            print(colored.magenta("Applying custom stack policy"))

    return stack_policy

def _get_stack_policy_during_update(override_stack_policy):
    if override_stack_policy:
        default_stack_policy_during_update = json.dumps({
              "Statement" : [
                {
                  "Effect" : "Allow",
                  "Action" : "Update:*",
                  "Principal": "*",
                  "Resource" : "*"
                }
              ]
            })
    else:
        default_stack_policy_during_update = json.dumps({
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "Update:Modify",
                    "Principal": "*",
                    "Resource": "*"
                },
                {
                    "Effect": "Deny",
                    "Action": ["Update:Replace", "Update:Delete"],
                    "Principal": "*",
                    "Resource": "*"
                }
            ]
        })

    stack_policy_during_update = default_stack_policy_during_update

    # check if a user specified his own stack policy
    if CLOUDFORMATION_FOUND:
        if "get_stack_policy_during_update" in dir(cloudformation):
            stack_policy_during_update = cloudformation.get_stack_policy_during_update()
            print(colored.magenta("Applying custom stack policy for updates\n"))

    return stack_policy_during_update


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
            StackPolicyBody=_get_stack_policy(),
        )
    # if we have no artifacts bucket configured then upload the template directly
    except ConfigMissingException:
        response = client_cf.create_stack(
            StackName=get_stack_name(conf),
            TemplateBody=cloudformation.generate_template(),
            Parameters=generate_parameters(conf),
            Capabilities=[
                'CAPABILITY_IAM',
            ],
            StackPolicyBody=_get_stack_policy(),
        )

    message = "kumo bot: created stack %s " % get_stack_name(conf)
    monitoring.slacker_notifcation("systemmessages", message, SLACK_TOKEN)
    stackname = get_stack_name(conf)
    exit_code = poll_stack_events(boto_session, stackname)
    call_post_create_hook()
    call_post_hook()
    sys.exit(exit_code)


# update stack with all the information we have

def update_stack(conf, override_stack_policy):
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
                StackPolicyBody=_get_stack_policy(),
                StackPolicyDuringUpdateBody=_get_stack_policy_during_update(override_stack_policy)

            )
        except ConfigMissingException:
            response = client_cf.update_stack(
                StackName=get_stack_name(conf),
                TemplateBody=cloudformation.generate_template(),
                Parameters=generate_parameters(conf),
                Capabilities=[
                    'CAPABILITY_IAM',
                ],
                StackPolicyBody=_get_stack_policy(),
                StackPolicyDuringUpdateBody=_get_stack_policy_during_update(override_stack_policy)
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
            print (type(e))
            print(colored.red("Exception occured during update:"+str(e)))



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
        string.ascii_uppercase) for _ in range(8))
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

def validate_import():
    if not CLOUDFORMATION_FOUND:
        print (colored.red("no cloudformation.py found, bailing out..."))
        sys.exit(1)


def main():
    arguments = docopt(doc)
    conf = None

    # Run command
    if arguments["deploy"]:
        validate_import()
        call_pre_hook()
        conf = read_config()
        print_parameter_diff(conf)
        are_credentials_still_valid(boto_session)
        if arguments["--override-stack-policy"]:
            override_stack_policy=True
        else:
            override_stack_policy=False
        deploy_stack(conf, override_stack_policy=override_stack_policy)
    elif arguments["delete"]:
        validate_import()
        conf = read_config()
        are_credentials_still_valid(boto_session)
        delete_stack(conf)
    elif arguments["validate"]:
        validate_import()
        conf = read_config()
        print_parameter_diff(conf)
        are_credentials_still_valid(boto_session)
        validate_stack()
    elif arguments["generate"]:
        validate_import()
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
        validate_import()
        conf = read_config()
        print_parameter_diff(conf)
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
