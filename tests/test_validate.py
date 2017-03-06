# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

from botocore.validate import validate_parameters
from botocore import xform_name
import pytest

from gcdt_testtools.helpers_aws import awsclient  # fixtures!


# note: this is not really a test
# this was made for documentation purposes on how to do parameter validation


def test_validate_parameters(awsclient):

    client_s3 = awsclient.get_client('s3')
    service_model = client_s3.meta.service_model
    #print(service_model.operation_names)

    operation_model = service_model.operation_model('HeadObject')

    params = {
        'foo': 'bar'
    }

    with pytest.raises(Exception) as einfo:
        validate_parameters(params, operation_model.input_shape)
    assert einfo.match(r'.*Missing required parameter in input: "Bucket".*')
    assert einfo.match(r'.*Missing required parameter in input: "Key".*')
    assert einfo.match(r'.*Unknown parameter in input: "foo".*')


def test_xform_name(awsclient):
    # Convert camel case to a "pythonic" name.
    assert xform_name('HeadObject') == 'head_object'


def test_pythonic_name(awsclient):
    # Convert "pythonic" name to camel case.
    # to convert back we need to create or cache the mapping like this:
    client_s3 = awsclient.get_client('s3')
    operation_names = client_s3.meta.service_model.operation_names
    mapping = {xform_name(on): on for on in operation_names}

    assert mapping['head_object'] == 'HeadObject'
