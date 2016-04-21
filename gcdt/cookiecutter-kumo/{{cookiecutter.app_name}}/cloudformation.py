#!/usr/bin/env python

import troposphere

from troposphere import Template

t = Template()

t.add_description(
    "AWS CloudFormation for {{cookiecutter.app_name}} "

)


def generate_template():
    return t.to_json()
