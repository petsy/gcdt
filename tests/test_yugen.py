# -*- coding: utf-8 -*-
import os
import textwrap
from nose.tools import assert_true, assert_equal, assert_not_in
from gcdt.yugen_core import _compile_template, _arn_to_uri, \
    _get_region_and_account_from_lambda_arn, _template_variables_to_dict
from .helpers import create_tempfile, with_setup_args


def _setup():
    return {'temp_files': []}


def _teardown(temp_files=[]):
    for t in temp_files:
        os.unlink(t)


@with_setup_args(_setup, _teardown)
def test_compile_template(temp_files):
    swagger_template_file = create_tempfile(textwrap.dedent("""\
        ---
          swagger: "2.0"
          info:
            title: {{apiName}}
            description: {{apiDescription}}
            version: "0.0.1"
          basePath: "/{{apiBasePath}}"
          host: "{{apiHostname}}"
    """))

    template_params = {
        'apiName': 'apiName',
        'apiDescription': 'apiDescription',
        'apiBasePath': 'apiBasePath',
        'apiHostname': 'apiHostname'
    }

    expected = textwrap.dedent("""\
        ---
          swagger: "2.0"
          info:
            title: apiName
            description: apiDescription
            version: "0.0.1"
          basePath: "/apiBasePath"
          host: "apiHostname"
    """)

    assert_equal(_compile_template(swagger_template_file, template_params),
                 expected)
    return {'temp_files': [swagger_template_file]}


def test_get_region_and_account_from_lambda_arn():
    lambda_arn = 'arn:aws:lambda:eu-west-1:644239850139:function:dp-dev-process-keyword-extraction'
    lambda_region, lambda_account_id = \
        _get_region_and_account_from_lambda_arn(lambda_arn)
    assert_equal(lambda_region, 'eu-west-1')
    assert_equal(lambda_account_id, '644239850139')


def test_arn_to_uri():
    lambda_arn = 'arn:aws:lambda:eu-west-1:644239850139:function:dp-dev-process-keyword-extraction'
    uri = _arn_to_uri(lambda_arn, 'ACTIVE')
    assert_equal(uri, 'arn:aws:apigateway:eu-west-1:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-1:644239850139:function:dp-dev-process-keyword-extraction:ACTIVE/invocations')


def test_template_variables_to_dict():
    api_name = 'apiName'
    api_description = 'apiDescription'
    api_target_stage = 'mock'

    result = _template_variables_to_dict(api_name, api_description, api_target_stage)
    assert_equal(result['apiName'], api_name)
    assert_equal(result['apiDescription'], api_description)
    assert_equal(result['apiBasePath'], 'mock')
    assert_not_in('apiHostname', result)


def test_template_variables_to_dict_custom_hostname():
    api_name = 'apiName'
    api_description = 'apiDescription'
    api_target_stage = 'mock'

    result = _template_variables_to_dict(api_name, api_description,
                                         api_target_stage, custom_hostname='chn',
                                         custom_base_path='cbp')
    assert_equal(result['apiName'], api_name)
    assert_equal(result['apiDescription'], api_description)
    assert_equal(result['apiBasePath'], 'cbp')
    assert_equal(result['apiHostname'], 'chn')
