# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import troposphere
from nose.tools import assert_equal
from gcdt.kumo_util import StackLookup


def test_StackLookup():
    # Create EC2 Cloudformation template with troposphere
    t = troposphere.Template()
    t.add_version('2010-09-09')
    t.add_description('gcdt unit-tests')

    lambda_lookup_arn = 'lookup:stack:%s:EC2BasicsLambdaArn' % 'dp-dev'
    stack_lookup = StackLookup(t, lambda_lookup_arn)
    # as_reference: Is the parameter a reference (Default) or a string
    vpcid = stack_lookup.get_att('vpcid', as_reference=False)
    assert vpcid.data == {'Fn::GetAtt': ['StackOutput', 'vpcid']}
