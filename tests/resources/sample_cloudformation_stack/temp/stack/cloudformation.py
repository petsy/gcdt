#!/usr/bin/env python

import troposphere

from troposphere import Template

t = Template()

t.add_description(
    "AWS CloudFormation for stack "

)


def generate_template():
    return t.to_json()
