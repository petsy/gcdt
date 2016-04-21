import logging
import json
from jsonserializer import json_serial

###################################
# General logging support for
# console and logfile
#
# Override globals before using setup_logger for customization


def setup_logger(
        disc_logging=False,
        logger_name="python-logger",
        logger_path="./",
        logging_level_root = logging.DEBUG,
        logging_level_console = logging.INFO,
        logging_level_file = logging.INFO
):
    log = logging.getLogger(logger_name)
    log.setLevel(logging_level_root)

    # create console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging_level_console)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    log.addHandler(ch)

    if disc_logging:
        fh = logging.FileHandler(logger_path + logger_name + '.log')
        fh.setFormatter(formatter)
        fh.setLevel(logging_level_file)
        log.addHandler(fh)

    return log


def log_json(log_entry_dict):
    return json.dumps(log_entry_dict, sort_keys=True,indent=4, separators=(',', ': '), default=json_serial)

log = setup_logger()
