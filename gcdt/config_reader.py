from pyhocon import ConfigFactory
from collections import OrderedDict, MutableMapping
from gcdt import servicediscovery
import os

#####################
# Reads a config in HOCON format.
#
# If local set ENV variable to LOCAL and it will use settings_local.conf
# Standard is no ENV variable and then it uses a settings.conf

# TODO FIX env handling: adapt ci tools to new method
# TODO read conf from path

ENV_LOCAL = "local"
ENV_PRODUCTION = "prod"
ENV_PRE_PRODUCTION = "preprod"
ENV_DEVELOP = "dev"


def read_config(config_base_name="settings", location="", do_lookups=True):
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


def get_env():
    """
    Read environment from ENV and mangle it to a (lower case) representation
    :return: Environment as lower case string (or None if not matched)
    """
    env = os.environ.get('ENV') if os.environ.get('ENV') is not None else os.environ.get('env')
    env = env.lower() if env is not None else None

    if env == ENV_LOCAL:
        return ENV_LOCAL
    elif env == ENV_DEVELOP:
        return ENV_DEVELOP
    elif env == ENV_PRODUCTION:
        return ENV_PRODUCTION
    elif env == ENV_PRE_PRODUCTION:
        return ENV_PRE_PRODUCTION

    return None


def get_config_name(config_base_name):
    """
    Read config file name based on ENV variable
    """
    env = get_env()
    env = "" if env is None else "_" + env

    return config_base_name + env + ".conf"


# TODO remove method. I think we should not make methods public only for testing - ludwigm
def resolve_lookups(config):
    return __resolve_lookups(config)


def __resolve_lookups(config):
    """
    Resolve all lookups in the config and return it transformed
    """
    dic = config.as_plain_ordered_dict()
    stackset = set(__identify_stacks_recurse(dic))
    stackdata = {}
    print stackset
    for stack in stackset:
        if "." in stack:
            stackdata.update({stack: {"sslcert": servicediscovery.get_ssl_certificate(stack)}})
        else:
            stackdata.update({stack: servicediscovery.get_outputs_for_stack(stack)})
    dict_resolved = __resolve_lookups_recurse(dic, stackdata)
    return dict_resolved


def __identify_stacks_recurse(dic):
    """
    Identify all stacks which are needed to be fetched
    """
    stacklist = []
    if isinstance(dic, OrderedDict):
        for key, value in dic.items():
            if isinstance(value, OrderedDict):
                stacklist = stacklist + (__identify_stacks_recurse(value))
            elif isinstance(value, list):
                for listelem in value:
                    stacklist = stacklist + (__identify_stacks_recurse(listelem))
            else:
                __identify_single_value(value, stacklist)

    else:
        __identify_single_value(dic, stacklist)
    return stacklist


def __identify_single_value(value, stacklist):
    if isinstance(value, basestring):
        if value.startswith("lookup:") or value.startswith("ssl:"):
            splits = value.split(":")
            stacklist.append(splits[1])


def __resolve_lookups_recurse(dic, stacks):
    subdict = OrderedDict()
    if isinstance(dic, OrderedDict):
        for key, value in dic.items():
            if isinstance(value, OrderedDict):
                subdict[key] = __resolve_lookups_recurse(value, stacks)
            elif isinstance(value, list):
                sublist = []
                for listelem in value:
                    print listelem
                    sublist.append(__resolve_lookups_recurse(listelem, stacks))
                subdict[key] = sublist
            else:
                subdict[key] = __resolve_single_value(value, stacks)
    else:
        return __resolve_single_value(dic, stacks)
    return subdict


def __resolve_single_value(value, stacks):
    if isinstance(value, basestring):
        if value.startswith("lookup:"):
            splits = value.split(":")
            return stacks[splits[1]][splits[2]]
        if value.startswith("ssl:"):
            splits = value.split(":")
            return stacks[splits[1]].values()[0]
    return value
