# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import os

from nose.tools import assert_dict_contains_subset,assert_in
from nose.tools import assert_equal, assert_is_not_none

import pytest

from gcdt.utils import get_context, execute_scripts

from .helpers_aws import awsclient
from . import here


@pytest.mark.aws
def test_get_context(awsclient):
    actual = get_context(awsclient, 'kumo', 'deploy')
    expected_subset = {
        'tool': 'kumo',
        'command': 'deploy',
        'env': 'dev',
    }
    assert_dict_contains_subset(expected_subset, actual)
    # the api_key is currently not rolled out see OPS-126
    # assert_in('_datadog_api_key', actual)
    assert_in('user', actual)
    assert_in('version', actual)


@pytest.mark.aws
def test_execute_scripts(awsclient):
    start_dir = here('.')
    codedeploy_dir = here('resources/sample_pre_bundle_script_codedeploy')
    os.chdir(codedeploy_dir)
    pre_bundle_scripts = ['pre_bundle_script/dummy_script.sh']
    assert_is_not_none(pre_bundle_scripts)
    exit_code = execute_scripts(pre_bundle_scripts)
    assert_equal(exit_code, 0)
    os.chdir(start_dir)


# TODO
'''
are_credentials_still_valid
'''