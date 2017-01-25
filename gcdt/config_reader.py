# -*- coding: utf-8 -*-

"""config_reader reads a config in HOCON format.

If local set ENV variable to LOCAL and it will use settings_local.conf
Standard is no ENV variable and then it uses a settings.conf
"""

from __future__ import print_function
import os
from pyhocon import ConfigFactory, HOCONConverter
from collections import OrderedDict
from .servicediscovery import get_ssl_certificate, get_outputs_for_stack, \
    get_base_ami
try:
    from credstash import get_secret
except ImportError:
    pass


# TODO FIX env handling: adapt ci tools to new method
# TODO read conf from path

ENV_LOCAL = "local"
ENV_PRODUCTION = "prod"
ENV_PRE_PRODUCTION = "preprod"
ENV_DEVELOP = "dev"

DEFAULT_LOOKUPS = ["secret", "ssl", "stack"]
VALID_OUTPUT_FORMATS = ["configtree", "hocon", "json", "properties", "yaml"]


def read_config(boto_session, config_base_name="settings", location="",
                lookups=DEFAULT_LOOKUPS, output_format='configtree',
                add_env=True):
    """
    :param config_base_name:
    :param location:
    :param lookups: array defining which values should be looked up (default all)
    :param output_format: string defining output format (default ConfigTree)
    :param add_env:
    :return:
    """
    return __read_config(boto_session, config_base_name, location, lookups,
                         output_format, add_env, fail_if_not_exists=True)


def read_config_if_exists(boto_session, config_base_name="settings", location="",
                          lookups=DEFAULT_LOOKUPS, output_format='configtree',
                          add_env=True):
    """
    :param config_base_name:
    :param location:
    :param lookups: array defining which values should be looked up (default all)
    :param output_format: string defining output format (default ConfigTree)
    :param add_env:
    :return:
    """
    return __read_config(boto_session, config_base_name, location, lookups,
                         output_format, add_env, fail_if_not_exists=False)


def __read_config(boto_session, config_base_name, location, lookups, output_format, add_env,
                  fail_if_not_exists):
    lookups = __parse_lookups(lookups)
    try:
        config_file_name = __resolve_dir(location) + \
                           get_config_name(config_base_name, add_env)
        config = ConfigFactory.parse_file(config_file_name)
        if lookups:
            try:
                config = ConfigFactory.from_dict(
                    __resolve_lookups(boto_session, config, lookups))
            except AttributeError:
                return config
        return format_conversion(config, output_format)
    except Exception as e:
        if fail_if_not_exists:
            print("couldn't read config file")
            print(e)
            raise
        else:
            d = OrderedDict()
            config = ConfigFactory.from_dict(d)
            return format_conversion(config, output_format)


def format_conversion(config, output_format):
    if output_format == "configtree":
        return config
    elif output_format in VALID_OUTPUT_FORMATS:
        return HOCONConverter.convert(config, output_format)


def read_lambda_config(boto_session, config_base_name="lambda", lookups=DEFAULT_LOOKUPS):
    return read_config(boto_session, config_base_name, lookups=lookups)


def read_api_config(boto_session, config_base_name="api", lookups=DEFAULT_LOOKUPS):
    return read_config(boto_session, config_base_name, lookups=lookups)


def get_env():
    """
    Read environment from ENV and mangle it to a (lower case) representation
    :return: Environment as lower case string (or None if not matched)
    """
    env = os.environ.get('ENV') if os.environ.get('ENV') is not None \
        else os.environ.get('env')
    env = env.lower() if env is not None else None

    # Deprecated: only used for DP!
    if env == ENV_LOCAL:
        return ENV_LOCAL
    elif env == ENV_DEVELOP:
        return ENV_DEVELOP
    elif env == ENV_PRODUCTION:
        return ENV_PRODUCTION
    elif env == ENV_PRE_PRODUCTION:
        return ENV_PRE_PRODUCTION

    return None


def get_config_name(config_base_name, add_env=True):
    """
    Read config file name based on ENV variable
    """
    if not add_env:
        return config_base_name + ".conf"

    env = os.environ.get('ENV') if os.environ.get('ENV') is not None \
        else os.environ.get('env')
    env = env.lower() if env is not None else ""
    env = "_" + env if env else ""

    return config_base_name + env + ".conf"


# TODO remove method. I think we should not make methods public only for
# testing - ludwigm
#def resolve_lookups(config, lookups):
#    return __resolve_lookups(config, lookups=lookups)


def __parse_lookups(lookups):
    if isinstance(lookups, list):
        valid_lookups = []
        for lookup in lookups:
            if lookup in DEFAULT_LOOKUPS:
                valid_lookups.append(lookup)
            else:
                print("ERROR parsing lookups: {} is not a valid lookup type.")
                raise
        return valid_lookups
    if isinstance(lookups, bool):
        if lookups:
            return DEFAULT_LOOKUPS
        else:
            return []


def __resolve_dir(location):
    if not location.startswith("/"):
        return os.getcwd() + "/" + location + "/"
    else:
        return location + "/"


def __resolve_lookups(boto_session, config, lookups):
    """
    Resolve all lookups in the config and return it transformed
    :param resolve_stack_only: bool if only lookup:stack entries are to be resolved
    """
    dic = config.as_plain_ordered_dict()
    stackset = set(__identify_stacks_recurse(dic, lookups))
    stackdata = {}

    for stack in stackset:
        if "." in stack and "ssl" in lookups:
            stackdata.update({stack: {"sslcert": get_ssl_certificate(stack)}})
        elif "stack" in lookups:
            stackdata.update({stack: get_outputs_for_stack(stack)})
    dict_resolved = __resolve_lookups_recurse(boto_session, dic, stackdata, lookups)
    return dict_resolved


def __identify_stacks_recurse(dic, lookups):
    """
    Identify all stacks which are needed to be fetched
    """
    stacklist = []
    if isinstance(dic, OrderedDict):
        for key, value in dic.items():
            if isinstance(value, OrderedDict):
                stacklist += __identify_stacks_recurse(value, lookups)
            elif isinstance(value, list):
                for listelem in value:
                    stacklist = stacklist + (
                        __identify_stacks_recurse(listelem, lookups))
            else:
                __identify_single_value(value, stacklist, lookups)

    else:
        __identify_single_value(dic, stacklist, lookups)
    return stacklist


def __identify_single_value(value, stacklist, lookups):
    if isinstance(value, basestring):
        if value.startswith("lookup:"):
            splits = value.split(":")
            if splits[1] == "stack" and "stack" in lookups:
                stacklist.append(splits[2])
            elif splits[1] == "ssl" and "ssl" in lookups:
                stacklist.append(splits[2])


def __resolve_lookups_recurse(boto_session, dic, stacks, lookups):
    subdict = OrderedDict()
    if isinstance(dic, OrderedDict):
        for key, value in dic.items():
            if isinstance(value, OrderedDict):
                subdict[key] = __resolve_lookups_recurse(boto_session, value,
                                                         stacks,lookups)
            elif isinstance(value, list):
                sublist = []
                for listelem in value:
                    sublist.append(
                        __resolve_lookups_recurse(boto_session, listelem,
                                                  stacks, lookups))
                subdict[key] = sublist
            else:
                subdict[key] = __resolve_single_value(boto_session, value,
                                                      stacks, lookups)
    else:
        return __resolve_single_value(boto_session, dic, stacks, lookups)
    return subdict


def __resolve_single_value(boto_session, value, stacks, lookups):
    if isinstance(value, basestring):
        if value.startswith("lookup"):
            splits = value.split(":")
            if splits[1] == "stack" and "stack" in lookups:
                return stacks[splits[2]][splits[3]]
            if splits[1] == "ssl" and  "ssl" in lookups:
                return stacks[splits[2]].values()[0]
            if splits[1] == "secret" and "secret" in lookups:
                return get_secret(boto_session, splits[2])
            if splits[1] == "baseami":
                return get_base_ami()
    return value
