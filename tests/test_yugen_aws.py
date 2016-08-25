# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import botocore.session

from nose.plugins.attrib import attr
from nose.tools import assert_equal, assert_greater_equal, \
    assert_in, assert_not_in, assert_regexp_matches

from gcdt.logger import setup_logger
from gcdt.yugen_core import deploy_api, delete_api, delete_api_key, \
    create_api_key

from .helpers import check_preconditions, random_string, with_setup_args

log = setup_logger(__name__)
# TODO: remove the slack token (see mail)
SLACK_TOKEN = '***REMOVED***'


def here(p): return os.path.join(os.path.dirname(__file__), p)


def _setup():
    check_preconditions()  # check whether required AWS env variables are set?
    return {}


def _teardown(api_keys=[], apis=[]):
    # delete apis
    for api_name in apis:
        delete_api(api_name, SLACK_TOKEN)
    # delete api keys
    for key in api_keys:
        delete_api_key(key)


@attr('aws')
@with_setup_args(_setup, _teardown)
def test_create_api():
    log.info('running test_create_api')
    boto_session = botocore.session.get_session()

    temp_string = random_string()
    api_name = 'unittest-gcdt-sample-api-%s' % temp_string
    api_key_name = 'unittest-gcdt-sample-api-key-%s' % temp_string
    api_description = 'Gcdt sample API based on dp api-mock'
    target_stage = 'mock'
    api_key = create_api_key(api_name, api_key_name)
    print(api_key)

    lambdas = []

    deploy_api(
        boto_session=boto_session,
        api_name=api_name,
        api_description=api_description,
        stage_name=target_stage,
        api_key=api_key,
        lambdas=lambdas,
        slack_token=SLACK_TOKEN
    )

    api_keys = [api_key]
    apis = [api_name]
    return {'api_keys': api_keys, 'apis': apis}


# FIXME: tests
# * important test "yugen deploy" without valid key, I think there is a defect!
# * get_lambdas
# * test that reads config from file
# * current coverage is 28% (that is not good enough!)
