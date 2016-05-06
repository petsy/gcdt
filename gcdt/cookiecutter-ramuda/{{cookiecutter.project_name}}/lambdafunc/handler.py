from __future__ import print_function

import json
import urllib
from {{cookiecutter.module_name}}_module import {{cookiecutter.module_name}}
print('Loading function')


def lambda_handler(event, context):
    if "ramuda_action" in event:
        if event["ramuda_action"] == "ping":
            return "alive"
    else:
        {{cookiecutter.module_name}}()
        return event