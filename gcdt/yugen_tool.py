#!/usr/bin/env python

import yugen_utils
from docopt import docopt
import boto3
import botocore.session
import os
import uuid
import json
import monitoring
from glomex_utils.config_reader import read_api_config
import utils

# creating docopt parameters and usage help
doc = """Usage:
        yugen deploy
        yugen delete -f
        yugen export
        yugen list
        yugen apikey-create <keyname>
        yugen apikey-list
        yugen apikey-delete
        yugen version

-h --help           show this
"""

# TODO support changing API keys
# TODO fill swagger description and name from config
# TODO support more than one lambda function
# TODO investigate base path problem


SWAGGER_FILE = "swagger.yaml"
YUGEN_CONFIG = yugen_utils.read_yugen_config()
SLACK_TOKEN = YUGEN_CONFIG.get("yugen.slack-token")

session = botocore.session.get_session()


def import_from_swagger(api_name, api_description):
    client = session.create_client('apigateway')

    print "import from swagger file"

    swagger_file = open(SWAGGER_FILE, 'r').read()
    swagger_file = swagger_file.replace("$API_NAME", api_name)
    swagger_file = swagger_file.replace("$API_DESCRIPTION", api_description)

    response_swagger = client.import_rest_api(
        failOnWarnings=True,
        body=swagger_file
    )

    print yugen_utils.json2table(response_swagger)


def update_from_swagger(api_name, api_description):
    client = session.create_client('apigateway')

    print "update from swagger file"

    swagger_file = open(SWAGGER_FILE, 'r').read()
    swagger_file = swagger_file.replace("$API_NAME", api_name)
    swagger_file = swagger_file.replace("$API_DESCRIPTION", api_description)

    api = yugen_utils.api_by_name(api_name)

    if api is not None:
        response_swagger = client.put_rest_api(
            restApiId=api["id"],
            mode="overwrite",
            failOnWarnings=True,
            body=swagger_file
        )
    else:
        print "API name unknown"

    print yugen_utils.json2table(response_swagger)


# WIP
# FIXME looks like it ignores that it should export yaml
def export_to_swagger(api_name, stage_name):
    client = session.create_client('apigateway')

    print "exporting to swagger"

    api = yugen_utils.api_by_name(api_name)

    if api is not None:
        print yugen_utils.json2table(api)

        response = client.get_export(
            restApiId=api["id"],
            stageName=stage_name,
            exportType="swagger",
            # parameters={
            #    'string': 'string'
            # },
            # accepts="application/yaml"
            accepts="application/json"
        )

        swagger_file = open("swagger_export.json", 'w')

        content = response["body"].read()

        swagger_file.write(content)
    else:
        print "API name unknown"


def list_apis():
    client = boto3.client('apigateway')

    apis = client.get_rest_apis()["items"]

    for api in apis:
        print yugen_utils.json2table(api)


def deploy_api(api_name, api_description, stage_name, api_key, lambdas):
    if not yugen_utils.api_exists(api_name):
        if os.path.isfile(SWAGGER_FILE):
            import_from_swagger(api_name, api_description)
        else:
            create_api(api_name=api_name, api_description=api_description)

        api = yugen_utils.api_by_name(api_name)

        if api is not None:
            for lmbda in lambdas:
                add_lambda_permissions(lmbda["name"], lmbda["alias"], api)
            create_deployment(api_name, stage_name)
            wire_api_key(api_name, api_key, stage_name)
            message = ("yugen bot: created api *%s*") % (api_name)
            monitoring.slacker_notifcation("systemmessages", message, SLACK_TOKEN)
        else:
            print "API name unknown"
    else:
        if os.path.isfile(SWAGGER_FILE):
            update_from_swagger(api_name, api_description)
        else:
            update_api()

        api = yugen_utils.api_by_name(api_name)

        if api is not None:
            create_deployment(api_name, stage_name)
            message = ("yugen bot: updated api *%s*") % (api_name)
            monitoring.slacker_notifcation("systemmessages", message, SLACK_TOKEN)
        else:
            print "API name unknown"


def create_api(api_name, api_description):
    client = boto3.client('apigateway')

    print "creating API"

    response = client.create_rest_api(
        name=api_name,
        description=api_description
    )

    print yugen_utils.json2table(response)


def delete_api(api_name):
    client = boto3.client('apigateway')

    print "deleting api: {}".format(api_name)
    api = yugen_utils.api_by_name(api_name)

    if api is not None:
        print yugen_utils.json2table(api)

        response = client.delete_rest_api(
            restApiId=api["id"]
        )

        print yugen_utils.json2table(response)
        message = ("yugen bot: deleted api *%s*") % (api_name)
        monitoring.slacker_notifcation("systemmessages", message, SLACK_TOKEN)
    else:
        print "API name unknown"


def wire_api_key(api_name, api_key, stage_name):
    client = boto3.client('apigateway')
    print "updating api key"

    api = yugen_utils.api_by_name(api_name)

    if api is not None:

        response = client.update_api_key(
            apiKey=api_key,
            patchOperations=[
                {
                    'op': 'add',
                    'path': '/stages',
                    'value': "{}/{}".format(api["id"], stage_name)
                },
            ]
        )

        print yugen_utils.json2table(response)
    else:
        print "API name unknown"


def update_api():
    print "updating api. not supported now"


def create_deployment(api_name, stage_name):
    client = boto3.client('apigateway')
    print "create deployment"

    api = yugen_utils.api_by_name(api_name)

    if api is not None:

        response = client.create_deployment(
            restApiId=api["id"],
            stageName=stage_name,
            description="TO BE FILLED"
        )

        print yugen_utils.json2table(response)
    else:
        print "API name unknown"


def create_api_key(api_name, api_key_name):
    client = boto3.client('apigateway')
    print "create api key: ".format(api_key_name)

    response = client.create_api_key(
        name=api_key_name,
        description="Created for " + api_name,
        enabled=True
    )

    print yugen_utils.json2table(response)

    print "Add this api key to your api.conf"


def delete_api_key(api_key):
    client = boto3.client('apigateway')
    print "delete api key: ".format(api_key)

    response = client.delete_api_key(
        apiKey=api_key
    )

    print yugen_utils.json2table(response)


def list_api_keys():
    client = boto3.client('apigateway')
    print "listing api keys"

    response = client.get_api_keys()["items"]

    for item in response:
        print yugen_utils.json2table(item)


def add_lambda_permissions(lambda_name, lambda_alias, api):
    client = boto3.client('lambda')

    print "Adding lambda permission for API Gateway"

    # lambda_full_name = lambda_name if lambda_alias is None else lambda_name + "/" + lambda_alias

    response_lamba = client.get_function(FunctionName=lambda_name)

    if response_lamba is not None:

        # Get info from the lambda instead of API Gateway as there is not other boto possibility
        lambda_arn = response_lamba["Configuration"]["FunctionArn"]
        lambda_region = lambda_arn.split(":")[3]
        lambda_account_id = lambda_arn.split(":")[4]

        source_arn = 'arn:aws:execute-api:{region}:{accountId}:{apiId}/*/*'.format(
            region=lambda_region,
            accountId=lambda_account_id,
            apiId=api["id"]
        )

        response = client.add_permission(
            FunctionName=lambda_name,
            StatementId=str(uuid.uuid1()),
            Action="lambda:InvokeFunction",
            Principal="apigateway.amazonaws.com",
            SourceArn=source_arn,
            Qualifier=lambda_alias
        )

        print yugen_utils.json2table(json.loads(response["Statement"]))
    else:
        print "Lambda function could not be found"


def get_lambdas(config):
    lambda_entries = config.get("lambda.entries", [])
    lmbdas = []
    for lambda_entry in lambda_entries:
        lmbda = {
            "name": lambda_entry.get("name", None),
            "alias": lambda_entry.get("alias", None)
        }
        lmbdas.append(lmbda)
    return lmbdas


def main():
    yugen_utils.are_credentials_still_valid()

    arguments = docopt(doc)

    if arguments["list"]:
        list_apis()
    elif arguments["deploy"]:
        conf = read_api_config()
        api_name = conf.get("api.name")
        api_description = conf.get("api.description")
        target_stage = conf.get("api.targetStage")
        api_key = conf.get("api.apiKey")
        lambdas = get_lambdas(conf)
        deploy_api(
            api_name=api_name,
            api_description=api_description,
            stage_name=target_stage,
            api_key=api_key,
            lambdas=lambdas
        )
    elif arguments["delete"]:
        conf = read_api_config()
        api_name = conf.get("api.name")
        delete_api(
            api_name=api_name
        )
    elif arguments["export"]:
        conf = read_api_config()
        api_name = conf.get("api.name")
        target_stage = conf.get("api.targetStage")
        export_to_swagger(
            api_name=api_name,
            stage_name=target_stage
        )
    elif arguments["apikey-create"]:
        conf = read_api_config()
        api_name = conf.get("api.name")
        create_api_key(api_name, arguments["<keyname>"])
    elif arguments["apikey-delete"]:
        conf = read_api_config()
        api_key = conf.get("api.apiKey")
        delete_api_key(api_key)
    elif arguments["apikey-list"]:
        list_api_keys()
    elif arguments["version"]:
        utils.version()


if __name__ == "__main__":
    main()
