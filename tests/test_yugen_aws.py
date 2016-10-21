# -*- coding: utf-8 -*-
from __future__ import print_function
import os

from nose.tools import assert_equal, assert_greater_equal, \
    assert_in, assert_not_in, assert_regexp_matches
import pytest

from gcdt.logger import setup_logger
from gcdt.yugen_core import deploy_api, delete_api, delete_api_key, \
    create_api_key
from . import helpers
from .helpers_aws import check_preconditions, boto_session

log = setup_logger(__name__)


def here(p): return os.path.join(os.path.dirname(__file__), p)


@pytest.fixture(scope='function')  # 'function' or 'module'
def cleanup_apis(boto_session):
    apis = []
    yield apis
    # cleanup
    for i in apis:
        delete_api(boto_session, i)


@pytest.fixture(scope='function')  # 'function' or 'module'
def cleanup_api_keys(boto_session):
    items = []
    yield items
    # cleanup
    for i in items:
        delete_api_key(boto_session, i)


@pytest.mark.aws
@check_preconditions
def test_create_api(boto_session, cleanup_api_keys, cleanup_apis):
    log.info('running test_create_api')

    temp_string = helpers.random_string()
    api_name = 'unittest-gcdt-sample-api-%s' % temp_string
    api_key_name = 'unittest-gcdt-sample-api-key-%s' % temp_string
    api_description = 'Gcdt sample API based on dp api-mock'
    target_stage = 'mock'
    api_key = create_api_key(boto_session, api_name, api_key_name)
    cleanup_api_keys.append(api_key)

    lambdas = []
    deploy_api(
        boto_session=boto_session,
        api_name=api_name,
        api_description=api_description,
        stage_name=target_stage,
        api_key=api_key,
        lambdas=lambdas
    )
    cleanup_apis.append(api_name)


# FIXME: tests
# * important test "yugen deploy" without valid key, I think there is a defect!
# * get_lambdas
# * test that reads config from file
# * current coverage is 28% (that is not good enough!)
