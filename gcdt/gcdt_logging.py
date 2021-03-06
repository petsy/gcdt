# -*- coding: utf-8 -*-
"""General logging support for console
"""
from __future__ import unicode_literals, print_function
import logging


class GcdtFormatter(logging.Formatter):
    """Give us details in case we use DEBUG level, for INFO no details.

    For WARN and ERROR output <level>: <msg>.
    Note: gcdt does NOT have a logfile!
    """
    # TODO this would be the central place to add colors. e.g. yellow for WARN
    # and red for ERROR
    # was: '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    FORMATS = {
        logging.DEBUG: "DEBUG: %(module)s: %(lineno)d: %(message)s",
        logging.INFO: "%(message)s",
        'DEFAULT': "%(levelname)s: %(message)s"
    }

    def format(self, record):
        self._fmt = self.FORMATS.get(record.levelno, self.FORMATS['DEFAULT'])
        return logging.Formatter.format(self, record)


# use logging.DictConfig which is the most convenient and hackable way
# to do logging configuration in Python.
logging_config = {
    'version': 1,
    'formatters': {
        'default': {
            '()': GcdtFormatter
        }
    },
    'handlers': {
        'default': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'stream': 'ext://sys.stdout'
        }
    },
    'loggers': {
        'gcdt': {
            'level': 'INFO',
            'handlers': ['default'],
            'propagate': 0
        },
        'gcdt_plugins': {
            'level': 'INFO',
            'handlers': ['default'],
            'propagate': 0
        }
    },
    'disable_existing_loggers': False
}


# TODO: I do not think this is used??
'''
def _json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    # Easy support to add ISO datetime
    # serialization for json.dumps
    if isinstance(obj, Decimal):
        return str(obj)

    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError("Type not serializable")


def log_json(log_entry_dict):
    return json.dumps(log_entry_dict, sort_keys=True, indent=4,
                      separators=(',', ': '), default=_json_serial)
'''
