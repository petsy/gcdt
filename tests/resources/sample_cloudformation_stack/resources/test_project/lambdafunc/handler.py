from __future__ import print_function

import json
import urllib
from test_module import test
print('Loading function')


def lambda_handler(event, context):
    if "ramuda_action" in event:
        if event["ramuda_action"] == "ping":
            return "alive"
    else:
        test()
        return event