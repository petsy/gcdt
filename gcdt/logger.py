# -*- coding: utf-8 -*-
"""General logging support for console and logfile

Override globals before using setup_logger for customization
"""

import logging
import json
from decimal import Decimal
from datetime import datetime


def setup_logger(
        disc_logging=False,
        logger_name="python-logger",
        logger_path="./",
        logging_level_root=logging.DEBUG,
        logging_level_console=logging.INFO,
        logging_level_file=logging.INFO
):
    log = logging.getLogger(logger_name)
    log.setLevel(logging_level_root)

    # create console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging_level_console)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    log.addHandler(ch)

    if disc_logging:
        fh = logging.FileHandler(logger_path + logger_name + '.log')
        fh.setFormatter(formatter)
        fh.setLevel(logging_level_file)
        log.addHandler(fh)

    return log


log = setup_logger()


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
