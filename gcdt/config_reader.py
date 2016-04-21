from pyhocon import ConfigFactory
import os

#####################
# Reads a config in HOCON format.
#
# If local set ENV variable to LOCAL and it will use settings_local.conf
# Standard is no ENV variable and then it uses a settings.conf

# TODO FIX env handling: only one way using outside variables or parameters
# TODO FIX env handling: have constants for parameters to reference in other parts
# TODO FIX env handling: use upper and lower case constants
# TODO FIX env handling: adapt ci tools to new method



def read_config(config_base_name = "settings"):
    """
    read local config file
    :param config_base_name:
    :return:
    """
    try:
        config_file_name = os.getcwd() + "/" + get_config_name(config_base_name)
        config = ConfigFactory.parse_file(config_file_name)
        return config
    except Exception as e:
        print("couldn't read config file")
        print(e)
        raise e


def read_lambda_config(config_base_name = "lambda"):
    return read_config(config_base_name)


def read_api_config(config_base_name = "api"):
    return read_config(config_base_name)


def get_config_name(config_base_name):
    env = os.environ.get('ENV')
    if env == "LOCAL":
        return config_base_name + "_local.conf"
    elif env == "DEV":
        return config_base_name + "_dev.conf"
    elif env == "PROD":
        return config_base_name + "_prod.conf"
    else:
        return config_base_name + ".conf"
