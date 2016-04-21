# Helper for api deploying

from pyhocon import ConfigFactory
from tabulate import tabulate
import boto3
import sys
from clint.textui import colored, prompt
import os



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


def api_exists(api_name):
    api = api_by_name(api_name)

    if api is None:
        return False

    return True


def api_by_name(api_name):
    client = boto3.client('apigateway')
    filtered_rest_apis = filter(lambda api: True if api["name"] == api_name else False, client.get_rest_apis()["items"])
    if len(filtered_rest_apis) > 1:
        raise Exception("more than one API with that name found. Clean up manually first")
    elif len(filtered_rest_apis) == 0:
        return None
    else:
        return filtered_rest_apis[0]


# TODO it is unused. Token is not read from config for now
def read_yugen_config():
    homedir = os.path.expanduser('~')
    kumo_config_file = homedir + "/" + ".yugen"
    try:
        config = ConfigFactory.parse_file(kumo_config_file)
        return config
    except Exception as e:
        print e
        print colored.red("Cannot find file .yugen in your home directory %s" % kumo_config_file)
        print colored.red("Please run 'yugen configure'")
        sys.exit(1)


def get_input():
    name = prompt.query('Please enter your Slack API token: ')
    return name

