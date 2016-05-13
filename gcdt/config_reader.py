from pyhocon import ConfigFactory
from collections import OrderedDict, MutableMapping
from gcdt import servicediscovery
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

# TODO read conf from path

def read_config(config_base_name="settings", location="", do_lookups=True):
    """
    read local config file
    :param do_lookups:
    :param config_base_name:
    :param location:
    :return:
    """
    try:
        config_file_name = os.getcwd() + "/" + location + "/" + get_config_name(config_base_name)
        config = ConfigFactory.parse_file(config_file_name)
        if do_lookups:
            config = ConfigFactory.from_dict(__resolve_lookups(config))
        return config
    except Exception as e:
        print("couldn't read config file")
        print(e)
        raise


def read_config_if_exists(config_base_name="settings", location="", do_lookups=True):
    """
    read local config file or return empty config
    :param do_lookups:
    :param location:
    :param config_base_name:
    :return:
    """
    try:
        config_file_name = os.getcwd() + "/" + location + "/" + get_config_name(config_base_name)
        config = ConfigFactory.parse_file(config_file_name)
        if do_lookups:
            config = ConfigFactory.from_dict(__resolve_lookups(config))
        return config
    except Exception as e:
        d = OrderedDict()
        config = ConfigFactory.from_dict(d)
        return config


def read_lambda_config(config_base_name="lambda"):
    return read_config(config_base_name)


def read_api_config(config_base_name="api"):
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

def resolve_lookups(config):
    return __resolve_lookups(config)

def __resolve_lookups(config):
    dic = config.as_plain_ordered_dict()
    stackset = set(__identify_stacks_recurse(dic))
    stackdata = {}
    for stack in stackset:
        if "." in stack:
            stackdata.update({stack:  {"sslcert": servicediscovery.get_ssl_certificate(stack)}})
        else:
            stackdata.update({stack: servicediscovery.get_outputs_for_stack(stack)})
    dict_resolved = __resolve_lookups_recurse(dic, stackdata)
    return dict_resolved


def __identify_stacks_recurse(dic):
    stacklist = []
    for key, value in dic.items():
        if isinstance(value, OrderedDict):
            stacklist = stacklist + (__identify_stacks_recurse(value))
        if not isinstance(value, OrderedDict):
            if value.startswith("lookup:"):
                splits = value.split(":")
                stacklist.append(splits[1])
            if value.startswith("ssl:"):
                splits = value.split(":")
                stacklist.append(splits[1])
    return stacklist


def __resolve_lookups_recurse(dic, stacks):
    subdict = OrderedDict()
    for key, value in dic.items():
        if isinstance(value, OrderedDict):
            subdict[key] = __resolve_lookups_recurse(value, stacks)
        if not isinstance(value, OrderedDict):
            if value.startswith("lookup:"):
                splits = value.split(":")
                value = stacks[splits[1]][splits[2]]
            subdict[key] = value
            if value.startswith("ssl:"):
                splits = value.split(":")
                value = stacks[splits[1]].values()[0]
            subdict[key] = value

    return subdict
