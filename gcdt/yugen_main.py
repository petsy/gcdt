#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

from docopt import docopt
import boto3

from .config_reader import read_api_config
from gcdt.yugen_core import list_api_keys, get_lambdas, delete_api, \
    export_to_swagger, create_api_key, list_apis, \
    create_custom_domain, delete_api_key, deploy_api
from gcdt.utils import version, read_gcdt_user_config, get_context, get_command, \
    check_gcdt_update
from gcdt.monitoring import datadog_notification, datadog_error, \
    datadog_event_detail


# creating docopt parameters and usage help
DOC = '''Usage:
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
'''


# TODO support changing API keys
# TODO investigate base path problem


def are_credentials_still_valid(boto_session):
    """Wrapper to bail out on invalid credentials."""
    from gcdt.yugen_core import are_credentials_still_valid as acsv
    exit_code = acsv(boto_session)
    if exit_code:
        sys.exit(1)


def get_user_config():
    slack_token, slack_channel = read_gcdt_user_config(
        compatibility_mode='kumo')
    if not slack_token and not isinstance(slack_token, basestring):
        sys.exit(1)
    else:
        return slack_token, slack_channel


def main():
    exit_code = 0
    boto_session = boto3.session.Session()
    arguments = docopt(DOC)
    check_gcdt_update()
    if arguments['version']:
        version()
        sys.exit(0)

    context = get_context(boto_session, 'yugen', get_command(arguments))
    datadog_notification(context)

    if arguments['list']:
        are_credentials_still_valid(boto_session)
        list_apis(boto_session)
    elif arguments['deploy']:
        slack_token, slack_channel = get_user_config()
        are_credentials_still_valid(boto_session)
        conf = read_api_config(boto_session)
        api_name = conf.get('api.name')
        api_description = conf.get('api.description')
        target_stage = conf.get('api.targetStage')
        api_key = conf.get('api.apiKey')
        lambdas = get_lambdas(boto_session, conf, add_arn=True)
        deploy_api(
            boto_session=boto_session,
            api_name=api_name,
            api_description=api_description,
            stage_name=target_stage,
            api_key=api_key,
            lambdas=lambdas,
            slack_token=slack_token,
            slack_channel=slack_channel
        )
        if 'customDomain' in conf:
            domain_name = conf.get('customDomain.domainName')
            route_53_record = conf.get('customDomain.route53Record')
            ssl_cert = {
                'name': conf.get('customDomain.certificateName'),
                'body': conf.get('customDomain.certificateBody'),
                'private_key': conf.get('customDomain.certificatePrivateKey'),
                'chain': conf.get('customDomain.certificateChain')
            }
            hosted_zone_id = conf.get('customDomain.hostedDomainZoneId')
            api_base_path = conf.get('customDomain.basePath')
            exit_code = create_custom_domain(
                boto_session=boto_session,
                api_name=api_name,
                api_target_stage=target_stage,
                api_base_path=api_base_path,
                domain_name=domain_name,
                route_53_record=route_53_record,
                ssl_cert=ssl_cert,
                hosted_zone_id=hosted_zone_id
            )
        event = 'yugen bot: deployed api *%s*' % api_name
        datadog_event_detail(context, event)
    elif arguments['delete']:
        slack_token, slack_channel = get_user_config()
        are_credentials_still_valid(boto_session)
        conf = read_api_config(boto_session)
        api_name = conf.get('api.name')
        delete_api(
            boto_session=boto_session,
            api_name=api_name,
            slack_token=slack_token,
            slack_channel=slack_channel
        )
        event = 'yugen bot: deleted api *%s*' % api_name
        datadog_event_detail(context, event)
    elif arguments['export']:
        are_credentials_still_valid(boto_session)
        conf = read_api_config(boto_session)
        api_name = conf.get('api.name')
        target_stage = conf.get('api.targetStage')
        api_description = conf.get('api.description')

        lambdas = get_lambdas(boto_session, conf, add_arn=True)
        export_to_swagger(
            boto_session=boto_session,
            api_name=api_name,
            stage_name=target_stage,
            api_description=api_description,
            lambdas=lambdas,
            custom_hostname=(conf.get('customDomain.domainName')
                             if 'customDomain' in conf else False),
            custom_base_path=(conf.get('customDomain.basePath')
                              if 'customDomain' in conf else False)
        )
    elif arguments['apikey-create']:
        are_credentials_still_valid(boto_session)
        conf = read_api_config(boto_session)
        api_name = conf.get('api.name')
        create_api_key(boto_session, api_name, arguments['<keyname>'])
    elif arguments['apikey-delete']:
        are_credentials_still_valid(boto_session)
        conf = read_api_config(boto_session)
        api_key = conf.get('api.apiKey')
        delete_api_key(boto_session, api_key)
    elif arguments['apikey-list']:
        are_credentials_still_valid(boto_session)
        list_api_keys(boto_session)
    elif arguments['custom-domain-create']:
        are_credentials_still_valid(boto_session)
        conf = read_api_config(boto_session)
        api_name = conf.get('api.name')
        api_target_stage = conf.get('api.targetStage')

        domain_name = conf.get('customDomain.domainName')
        route_53_record = conf.get('customDomain.route53Record')
        api_base_path = conf.get('customDomain.basePath')
        ssl_cert = {
            'name': conf.get('customDomain.certificateName'),
            'body': conf.get('customDomain.certificateBody'),
            'private_key': conf.get('customDomain.certificatePrivateKey'),
            'chain': conf.get('customDomain.certificateChain')
        }
        hosted_zone_id = conf.get('customDomain.hostedDomainZoneId')

        exit_code = create_custom_domain(
            boto_session=boto_session,
            api_name=api_name,
            api_target_stage=api_target_stage,
            api_base_path=api_base_path,
            domain_name=domain_name,
            route_53_record=route_53_record,
            ssl_cert=ssl_cert,
            hosted_zone_id=hosted_zone_id
        )

    if exit_code:
        datadog_error(context)
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
