#!/usr/bin/env python

import yugen_utils
from docopt import docopt
import boto3
import botocore.session
import os
import uuid
import json
import monitoring
from glomex_utils.config_reader import read_api_config, get_env
from dphelper.jsonserializer import json_serial
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
        yugen custom-domain-create
        yugen version

-h --help           show this
"""

# TODO support changing API keys
# TODO investigate base path problem

SWAGGER_FILE = "swagger.yaml"
YUGEN_CONFIG = yugen_utils.read_yugen_config()
SLACK_TOKEN = YUGEN_CONFIG.get("yugen.slack-token")

session = botocore.session.get_session()


def import_from_swagger(api_name, api_description, stage_name, lambdas):
    client = session.create_client('apigateway')

    print "Import from swagger file"

    api = yugen_utils.api_by_name(api_name)
    if api is not None:
        print yugen_utils.json2table(api)
        api_id = api["id"]
        template_variables = template_variables_to_dict(api_name,
                                                        api_description,
                                                        stage_name,
                                                        api_id,
                                                        lambdas)
        filled_swagger_file = yugen_utils.compile_template(SWAGGER_FILE, template_variables)
        response_swagger = client.import_rest_api(
            failOnWarnings=True,
            body=filled_swagger_file
        )
        print yugen_utils.json2table(response_swagger)
    else:
        print "API name unknown"


def update_from_swagger(api_name, api_description, stage_name, lambdas):
    client = session.create_client('apigateway')

    print "update from swagger file"

    api = yugen_utils.api_by_name(api_name)

    if api is not None:
        api_id = api["id"]
        template_variables = template_variables_to_dict(api_name,
                                                        api_description,
                                                        stage_name,
                                                        api_id,
                                                        lambdas)
        filled_swagger_file = yugen_utils.compile_template(SWAGGER_FILE, template_variables)

        response_swagger = client.put_rest_api(
            restApiId=api["id"],
            mode="overwrite",
            failOnWarnings=True,
            body=filled_swagger_file
        )
    else:
        print "API name unknown"

    print yugen_utils.json2table(response_swagger)


# WIP
def export_to_swagger(api_name, stage_name, api_description, lambdas):
    print "Exporting to swagger..."

    api = yugen_utils.api_by_name(api_name)
    if api is not None:

        print yugen_utils.json2table(api)
        api_id = api["id"]
        template_variables = template_variables_to_dict(api_name,
                                                        api_description,
                                                        stage_name,
                                                        api_id,
                                                        lambdas)
        content = yugen_utils.compile_template(SWAGGER_FILE, template_variables)
        swagger_file = open("swagger_export.yaml", 'w')

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
            import_from_swagger(api_name, api_description, stage_name, lambdas)
        else:
            create_api(api_name=api_name, api_description=api_description)

        api = yugen_utils.api_by_name(api_name)

        if api is not None:
            for lmbda in lambdas:
                add_lambda_permissions(lmbda, api)
            create_deployment(api_name, stage_name)
            wire_api_key(api_name, api_key, stage_name)
            message = ("yugen bot: created api *%s*") % (api_name)
            monitoring.slacker_notifcation("systemmessages", message, SLACK_TOKEN)
        else:
            print "API name unknown"
    else:
        if os.path.isfile(SWAGGER_FILE):
            update_from_swagger(api_name, api_description, stage_name, lambdas)
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


def create_custom_domain(api_name, api_target_stage, api_base_path, domain_name, route_53_record,
                         ssl_cert, hosted_zone_id):
    print("incoming settings:")
    print api_name
    print api_target_stage
    print  api_base_path
    print domain_name
    print route_53_record
    for key in ssl_cert:
        print " {}  <secret> ".format(key)
    print hosted_zone_id

    api_base_path = yugen_utils.basepath_to_string_if_null(api_base_path)
    api = yugen_utils.api_by_name(api_name)

    if not api:
        print("Api {} does not exist, aborting...".format(api_name))
        return

    domain = yugen_utils.custom_domain_name_exists(domain_name)

    if not domain:
        response = create_new_custom_domain(domain_name, ssl_cert)
        cloudfront_distribution= response["distributionDomainName"]
    else:
        cloudfront_distribution = domain["distributionDomainName"]

    if base_path_mapping_exists(domain_name, api_base_path):
        ensure_correct_base_path_mapping(domain_name, api_base_path, api["id"], api_target_stage)
    else:
        create_base_path_mapping(domain_name, api_base_path, api_target_stage, api["id"])

    record_exists, record_correct = record_exists_and_correct(hosted_zone_id, route_53_record, cloudfront_distribution)
    if record_correct:
        print("Route53 record correctly set: {} --> {}".format(route_53_record,
                                                               cloudfront_distribution))
    else:
        ensure_correct_route_53_record(hosted_zone_id,record_name=route_53_record, record_value=cloudfront_distribution)


def ensure_correct_route_53_record(hosted_zone_id, record_name, record_value, record_type="CNAME"):
    route_53_client = boto3.client("route53")
    response = route_53_client.change_resource_record_sets(
        HostedZoneId=hosted_zone_id,
        ChangeBatch={
            "Changes":[
                {
                    "Action": "UPSERT",
                    "ResourceRecordSet": {
                        "Name": (record_name + "."),
                        "Type": record_type,
                        "ResourceRecords": [
                            {
                                "Value": record_value
                            }
                        ],
                        "TTL": 300
                    }
                }
            ]
        }
    )


def ensure_correct_base_path_mapping(domain_name, base_path, api_id, target_stage):
    client = boto3.client("apigateway")
    mapping = client.get_base_path_mapping(domainName=domain_name,basePath=base_path)
    operations = []
    if not mapping["stage"] == target_stage:
        operations.append({
            "op":"replace",
            "path":"/stage",
            "value":target_stage
        })
    if not mapping["restApiId"] == api_id:
        operations.append({
            "op":"replace",
            "path":"/restApiId",
            "value":api_id
        })
    if operations:
        response = client.update_base_path_mapping(
            domainName=domain_name,
            basePath="(none)",
            patchOperations=operations)


def base_path_mapping_exists(domain_name, base_path):
    client = boto3.client("apigateway")
    base_path_mappings = client.get_base_path_mappings(domainName=domain_name)
    mapping_exists = False
    if base_path_mappings.get("items"):
        for item in base_path_mappings["items"]:
            if item["basePath"] == base_path:
                mapping_exists = True
    return mapping_exists

def create_base_path_mapping(domain_name, base_path, stage, api_id):
    client = boto3.client("apigateway")
    base_path_respone = client.create_base_path_mapping(
        domainName=domain_name,
        basePath=base_path,
        restApiId=api_id,
        stage=stage
    )

def record_exists_and_correct(hosted_zone_id, target_route_53_record_name, cloudfront_distribution):
    route_53_client = boto3.client("route53")
    response = route_53_client.list_resource_record_sets(
        HostedZoneId=hosted_zone_id
    )
    resource_records = response["ResourceRecordSets"]
    record_exists = False
    record_correct = False
    for record in resource_records:
        if record["Name"] == (target_route_53_record_name + "."):
            record_exists = True
            for value in record["ResourceRecords"]:
                if value["Value"] == cloudfront_distribution:
                    record_correct = True
    return record_exists, record_correct



def create_new_custom_domain(domain_name, ssl_cert):
    client = boto3.client("apigateway")
    response = client.create_domain_name(
        domainName=domain_name,
        certificateName=ssl_cert["name"],
        certificateBody=ssl_cert["body"],
        certificatePrivateKey=ssl_cert["private_key"],
        certificateChain=ssl_cert["chain"]
    )
    return response


def template_variables_to_dict(api_name, api_description, api_target_stage, api_id, lambdas):
    if lambdas:
        lambda_region, lambda_account_id = yugen_utils.get_region_and_account_from_lambda_arn(
            lambdas[0].get("arn")
        )
    else:
        boto3_session = boto3.session.Session()
        lambda_region = boto3_session.region_name
    api_hostname = api_id + ".execute-api." + lambda_region + ".amazonaws.com"

    return_dict = {
        "apiName": api_name,
        "apiDescription": api_description,
        "apiTargetStage": api_target_stage,
        "apiHostname": api_hostname
    }
    for lmbda in lambdas:
        if lmbda.get("arn"):
            lambda_uri = yugen_utils.arn_to_uri(lmbda["arn"], lmbda["alias"])
            return_dict.update({"{}".format(lmbda["swagger_ref"]): lambda_uri})
    return return_dict


def add_lambda_permissions(lmbda, api):
    client = boto3.client('lambda')

    print "Adding lambda permission for API Gateway"

    # lambda_full_name = lambda_name if lambda_alias is None else lambda_name + "/" + lambda_alias

    if lmbda.get("arn"):

        # Get info from the lambda instead of API Gateway as there is not other boto possibility
        lambda_arn = lmbda.get("arn")
        lambda_alias = lmbda.get("alias")
        lambda_name = lmbda.get("name")

        lambda_region, lambda_account_id = yugen_utils.get_region_and_account_from_lambda_arn(lambda_arn)

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


def get_lambdas(config, add_arn=False):
    client = boto3.client('lambda')
    lambda_entries = config.get("lambda.entries", [])
    lmbdas = []
    for lambda_entry in lambda_entries:
        lmbda = {
            "name": lambda_entry.get("name", None),
            "alias": lambda_entry.get("alias", None),
            "swagger_ref": lambda_entry.get("swaggerRef", None)
        }
        if add_arn:
            response_lambda = client.get_function(FunctionName=lmbda["name"])
            lmbda.update({"arn": response_lambda["Configuration"]["FunctionArn"]})
        lmbdas.append(lmbda)
    return lmbdas


    if conf.get("customDomain"):
        domain_name = conf.get("customDomain.domainName")
        route_53_record = conf.get("customDomain.route53Record")
        ssl_cert = {
        "name": conf.get("customDomain.certificateName"),
        "body": conf.get("customDomain.certificateBody"),
        "private_key": conf.get("customDomain.certificatePrivateKey"),
        "chain": conf.get("customDomain.certificateChain")
        }

        hosted_zone_id = conf.get("customDomain.hostedDomainZoneId")



def main():

    arguments = docopt(doc)

    if arguments["list"]:
        yugen_utils.are_credentials_still_valid()
        list_apis()
    elif arguments["deploy"]:
        yugen_utils.are_credentials_still_valid()
        conf = read_api_config()
        api_name = conf.get("api.name")
        api_description = conf.get("api.description")
        target_stage = conf.get("api.targetStage")
        api_key = conf.get("api.apiKey")
        lambdas = get_lambdas(conf, add_arn=True)
        deploy_api(
            api_name=api_name,
            api_description=api_description,
            stage_name=target_stage,
            api_key=api_key,
            lambdas=lambdas
        )
        if conf.get("customDomain"):
            domain_name = conf.get("customDomain.domainName")
            route_53_record = conf.get("customDomain.route53Record")
            ssl_cert = {
                "name": conf.get("customDomain.certificateName"),
                "body": conf.get("customDomain.certificateBody"),
                "private_key": conf.get("customDomain.certificatePrivateKey"),
                "chain": conf.get("customDomain.certificateChain")
            }
            hosted_zone_id = conf.get("customDomain.hostedDomainZoneId")
            api_base_path = conf.get("api.stage")
            create_custom_domain(api_name=api_name,
                                 api_target_stage=target_stage,
                                 api_base_path=api_base_path,
                                 domain_name=domain_name,
                                 route_53_record=route_53_record,
                                 ssl_cert=ssl_cert,
                                 hosted_zone_id=hosted_zone_id)
    elif arguments["delete"]:
        yugen_utils.are_credentials_still_valid()
        conf = read_api_config()
        api_name = conf.get("api.name")
        delete_api(
            api_name=api_name
        )
    elif arguments["export"]:
        yugen_utils.are_credentials_still_valid()
        conf = read_api_config()
        api_name = conf.get("api.name")
        target_stage = conf.get("api.targetStage")
        api_description = conf.get("api.description")

        lambdas = get_lambdas(conf, add_arn=True)
        export_to_swagger(
            api_name=api_name,
            stage_name=target_stage,
            api_description=api_description,
            lambdas=lambdas
        )
    elif arguments["apikey-create"]:
        yugen_utils.are_credentials_still_valid()
        conf = read_api_config()
        api_name = conf.get("api.name")
        create_api_key(api_name, arguments["<keyname>"])
    elif arguments["apikey-delete"]:
        yugen_utils.are_credentials_still_valid()
        conf = read_api_config()
        api_key = conf.get("api.apiKey")
        delete_api_key(api_key)
    elif arguments["apikey-list"]:
        yugen_utils.are_credentials_still_valid()
        list_api_keys()
    elif arguments["custom-domain-create"]:
        yugen_utils.are_credentials_still_valid()
        conf = read_api_config()
        api_name = conf.get("api.name")
        api_target_stage = conf.get("api.targetStage")
        api_base_path = conf.get("api.targetStage")

        domain_name = conf.get("customDomain.domainName")
        route_53_record = conf.get("customDomain.route53Record")
        ssl_cert = {
            "name": conf.get("customDomain.certificateName"),
            "body": conf.get("customDomain.certificateBody"),
            "private_key": conf.get("customDomain.certificatePrivateKey"),
            "chain": conf.get("customDomain.certificateChain")
        }
        hosted_zone_id = conf.get("customDomain.hostedDomainZoneId")

        create_custom_domain(api_name=api_name,
                             api_target_stage=api_target_stage,
                             api_base_path=api_base_path,
                             domain_name=domain_name,
                             route_53_record=route_53_record,
                             ssl_cert=ssl_cert,
                             hosted_zone_id=hosted_zone_id)

    elif arguments["version"]:
        utils.version()


if __name__ == "__main__":
    main()
