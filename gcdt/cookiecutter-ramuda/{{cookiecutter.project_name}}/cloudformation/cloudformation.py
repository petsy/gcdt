#!/usr/bin/env python

import troposphere

from troposphere import Template

t = Template()

t.add_description(
    "AWS CloudFormation for {{cookiecutter.app_name}} "

)


def generate_template():
    return t.to_json()



def post_hook():
    sample_hook.post_hook()


def post_update_hook():
    print("i'm a post update hook")


def post_create_hook():
    print("i'm a post create hook")