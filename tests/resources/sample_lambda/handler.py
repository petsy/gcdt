"""
Lambda example with external dependency
"""

import logging
from impl.sample import butaris_sample

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handle(event, context):
    """
    Lambda handler
    """
    logger.info("%s - %s", event, context)

    butaris_sample()
    
    return event
