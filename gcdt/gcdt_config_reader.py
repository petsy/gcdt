# -*- coding: utf-8 -*-
"""config_reader reads a config injson format.
"""
from __future__ import unicode_literals, print_function
import json
# TODO write config_reader for 'gcdt_<env>.json'


def read_json_config(config_file):
    # currently this is only a helper for test
    with open(config_file) as jfile:
        data = json.load(jfile)
    return data


'''
from collections import OrderedDict
import os

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
from base64 import b64encode, b64decode
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Hash.HMAC import HMAC
from Crypto.Util import Counter

from pyhocon import ConfigFactory, HOCONConverter
import botocore.exceptions

from .servicediscovery import get_ssl_certificate, get_outputs_for_stack, \
    get_base_ami

# TODO FIX env handling: adapt ci tools to new method
# TODO read conf from path

ENV_LOCAL = "local"
ENV_PRODUCTION = "prod"
ENV_PRE_PRODUCTION = "preprod"
ENV_DEVELOP = "dev"

DEFAULT_LOOKUPS = ["secret", "ssl", "stack"]
VALID_OUTPUT_FORMATS = ["configtree", "hocon", "json", "properties", "yaml"]


def read_config(awsclient, config_base_name="settings", location="",
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
    return __read_config(awsclient, config_base_name, location, lookups,
                         output_format, add_env, fail_if_not_exists=True)


def read_config_if_exists(awsclient, config_base_name="settings", location="",
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
    return __read_config(awsclient, config_base_name, location, lookups,
                         output_format, add_env, fail_if_not_exists=False)


def __read_config(awsclient, config_base_name, location, lookups,
                  output_format, add_env, fail_if_not_exists):
    lookups = __parse_lookups(lookups)
    try:
        config_file_name = __resolve_dir(location) + \
                           get_config_name(config_base_name, add_env)
        config = ConfigFactory.parse_file(config_file_name)
        if lookups:
            try:
                config = ConfigFactory.from_dict(
                    __resolve_lookups(awsclient, config, lookups))
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


def read_lambda_config(awsclient, config_base_name="lambda",
                       lookups=DEFAULT_LOOKUPS):
    return read_config(awsclient, config_base_name, lookups=lookups)


def read_api_config(awsclient, config_base_name="api", lookups=DEFAULT_LOOKUPS):
    return read_config(awsclient, config_base_name, lookups=lookups)


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


def __resolve_lookups(awsclient, config, lookups):
    """
    Resolve all lookups in the config and return it transformed
    :param resolve_stack_only: bool if only lookup:stack entries are to be resolved
    """
    dic = config.as_plain_ordered_dict()
    stackset = set(__identify_stacks_recurse(dic, lookups))
    stackdata = {}

    for stack in stackset:
        if "." in stack and "ssl" in lookups:
            stackdata.update({stack:
                                  {"sslcert":
                                       get_ssl_certificate(awsclient, stack)
                                   }
                              })
        elif "stack" in lookups:
            stackdata.update({stack: get_outputs_for_stack(awsclient, stack)})
    dict_resolved = __resolve_lookups_recurse(awsclient, dic, stackdata,
                                              lookups)
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


def __resolve_lookups_recurse(awsclient, dic, stacks, lookups):
    subdict = OrderedDict()
    if isinstance(dic, OrderedDict):
        for key, value in dic.items():
            if isinstance(value, OrderedDict):
                subdict[key] = __resolve_lookups_recurse(awsclient, value,
                                                         stacks, lookups)
            elif isinstance(value, list):
                sublist = []
                for listelem in value:
                    sublist.append(
                        __resolve_lookups_recurse(awsclient, listelem,
                                                  stacks, lookups))
                subdict[key] = sublist
            else:
                subdict[key] = __resolve_single_value(awsclient, value,
                                                      stacks, lookups)
    else:
        return __resolve_single_value(awsclient, dic, stacks, lookups)
    return subdict


def __resolve_single_value(awsclient, value, stacks, lookups):
    if isinstance(value, basestring):
        if value.startswith("lookup"):
            splits = value.split(":")
            if splits[1] == "stack" and "stack" in lookups:
                return stacks[splits[2]][splits[3]]
            if splits[1] == "ssl" and "ssl" in lookups:
                return stacks[splits[2]].values()[0]
            if splits[1] == "secret" and "secret" in lookups:
                return get_secret(awsclient, splits[2])
            if splits[1] == "baseami":
                # TODO this has a hardcoded account_id!!
                return get_base_ami(awsclient)
    return value


# needed to be copied from credstash in order to make it work with awsclient
class KmsError(Exception):
    def __init__(self, value=""):
        self.value = "KMS ERROR: " + value if value is not "" else "KMS ERROR"

    def __str__(self):
        return self.value


class IntegrityError(Exception):
    def __init__(self, value=""):
        self.value = "INTEGRITY ERROR: " + value if value is not "" else \
            "INTEGRITY ERROR"

    def __str__(self):
        return self.value


class ItemNotFound(Exception):
    pass


def get_secret(awsclient, name, version="",  # region=None,
                table="credential-store", context=None,
               **kwargs):
    """
    fetch and decrypt the secret called `name`
    """
    if context is None:
        context = {}
    client_ddb = awsclient.get_client('dynamodb')

    if version == "":
        # do a consistent fetch of the credential with the highest version
        # note KeyConditionExpression: Key("name").eq(name))
        response = client_ddb.query(
            TableName=table,
            Limit=1,
            ScanIndexForward=False,
            ConsistentRead=True,
            KeyConditionExpression='#S = :val',
            ExpressionAttributeNames={'#S': 'name'},
            ExpressionAttributeValues={':val': {'S': name}}
        )
        if response["Count"] == 0:
            raise ItemNotFound("Item {'name': '%s'} couldn't be found." % name)
        material = response["Items"][0]
    else:
        response = client_ddb.get_item(
            TableName=table,
            Key={
                "name": {'S': name},
                "version": {'S': version}
                }
        )
        if "Item" not in response:
            raise ItemNotFound(
                "Item {'name': '%s', 'version': '%s'} couldn't be found." % (
                    name, version))
        material = response["Item"]

    kms = awsclient.get_client('kms')
    # Check the HMAC before we decrypt to verify ciphertext integrity
    try:
        kms_response = kms.decrypt(CiphertextBlob=b64decode(material['key']['S']),
                                   EncryptionContext=context)

    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "InvalidCiphertextException":
            if context is None:
                msg = (
                    "Could not decrypt hmac key with KMS. The credential may "
                    "require that an encryption context be provided to decrypt "
                    "it.")
            else:
                msg = ("Could not decrypt hmac key with KMS. The encryption "
                       "context provided may not match the one used when the "
                       "credential was stored.")
        else:
            msg = "Decryption error %s" % e
        raise KmsError(msg)
    except Exception as e:
        raise KmsError("Decryption error %s" % e)
    key = kms_response['Plaintext'][:32]
    hmac_key = kms_response['Plaintext'][32:]
    hmac = HMAC(hmac_key, msg=b64decode(material['contents']['S']),
                digestmod=SHA256)
    if hmac.hexdigest() != material['hmac']['S']:
        raise IntegrityError("Computed HMAC on %s does not match stored HMAC"
                             % name)
    dec_ctr = Counter.new(128)
    decryptor = AES.new(key, AES.MODE_CTR, counter=dec_ctr)
    plaintext = decryptor.decrypt(b64decode(material['contents']['S'])).decode(
        "utf-8")
    return plaintext
'''
