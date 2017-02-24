# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

import troposphere

from gcdt.iam import IAMRoleAndPolicies


# TODO: write the tests!


def test_iam_role_and_policies():
    # used in cloudformation!
    # Config
    ROLE_NAME_PREFIX = 'lambda-'
    ROLE_PRINCIPALS = ['lambda.amazonaws.com']
    ROLE_PATH = '/lambda/'
    name = 'embed-player-wrapper'
    policy_lambda = 'arn:aws:iam::aws:policy/service-role/AWSLambdaRole'

    t = troposphere.Template()
    iam = IAMRoleAndPolicies(t, ROLE_NAME_PREFIX, ROLE_PRINCIPALS, ROLE_PATH)

    role_embed_player_wrapper = iam.build_role(
        name,
        [
            troposphere.Ref(policy_lambda)
        ]
    )
    assert role_embed_player_wrapper.to_dict()['Type'] == 'AWS::IAM::Role'

