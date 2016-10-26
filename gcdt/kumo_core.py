# -*- coding: utf-8 -*-
from __future__ import print_function
import imp
import json
import os
import random
import six
import string
import sys
import time
from datetime import tzinfo, timedelta, datetime

from clint.textui import colored, prompt
import pyhocon.exceptions
from pyhocon.exceptions import ConfigMissingException
from pyspin.spin import Default, Spinner
from tabulate import tabulate

from gcdt import monitoring
from glomex_utils.config_reader import get_env


def load_cloudformation_template(path=None):
    """Load cloudformation template from path.

    :param path: Absolute or relative path of cloudformation template. Defaults to cwd.
    :return: module, success
    """
    if not path:
        path = os.path.abspath('cloudformation.py')
    else:
        path = os.path.abspath(path)
    if isinstance(path, six.string_types):
        try:
            # TODO: provide version for Python 3.5 (importlib.util)
            sp = sys.path
            # temporarily add folder to allow relative path
            sys.path.append(os.path.abspath(os.path.dirname(path)))
            cloudformation = imp.load_source('cloudformation', path)
            sys.path = sp  # restore
            return cloudformation, True
        except ImportError as e:
            print('could not find package for import: %s' % e)
        except Exception as e:
            print('could not import cloudformation.py, maybe something wrong ',
                  'with your code?')
            print(e)
    return None, False


def print_parameter_diff(boto_session, config, out=sys.stdout):
    """print differences between local config and currently active config
    """
    cf = boto_session.resource('cloudformation')
    try:
        stackname = config['cloudformation.StackName']
        stack = cf.Stack(stackname)
        stack.load()  # load to trigger exception if the stack does not exist
    except pyhocon.exceptions.ConfigMissingException:
        print('StackName is not configured, could not create parameter diff',
              file=out)
        return None
    except:
        # probably the stack is not existent
        return None

    changed = 0
    table = []
    table.append(['Parameter', 'Current Value', 'New Value'])

    # Check if there are parameters for the stack
    if stack.parameters is not None:

        for param in stack.parameters:
            try:
                old = param['ParameterValue']
                if ',' in old:
                    old = old.split(',')
                new = config.get('cloudformation.' + param['ParameterKey'])
                if old != new:
                    table.append([param['ParameterKey'], old, new])
                    changed += 1
            except pyhocon.exceptions.ConfigMissingException:
                print('Did not find %s in local config file' % param['ParameterKey'],
                      file=out)

    if changed > 0:
        print(tabulate(table, tablefmt='fancy_grid'), file=out)
        print(colored.red('Parameters have changed. Waiting 10 seconds. \n'),
              file=out)
        print('If parameters are unexpected you might want to exit now: control-c',
              file=out)
        # Choose a spin style.
        spin = Spinner(Default)
        # Spin it now.
        for i in range(100):
            print(u'\r{0}'.format(spin.next()), end='', file=out)
            sys.stdout.flush()
            time.sleep(0.1)
        print('\n', file=out)


def _call_hook(boto_session, config, stack_name, parameters, cloudformation,
               hook, message=None, out=sys.stdout):
    if hook not in ['pre_hook', 'pre_create_hook', 'pre_update_hook',
                    'post_create_hook', 'post_update_hook', 'post_hook']:
        print(colored.green('Unknown hook: %s' % hook), file=out)
        return
    if not hasattr(cloudformation, hook):
        # hook is not present
        return
    if not message:
        message = 'Executing %s...' % hook.replace('_', ' ')
    print(colored.green(message), file=out)
    hook_func = getattr(cloudformation, hook)
    if not hook_func.func_code.co_argcount:
        hook_func()  # for compatibility with existing templates
    else:
        # new call for templates with parametrized hooks
        cfn_client = boto_session.client('cloudformation')
        stack_outputs = _get_stack_outputs(cfn_client, stack_name)
        stack_state = _get_stack_state(cfn_client, stack_name)
        hook_func(boto_session=boto_session, config=config,
                  parameters=parameters, stack_outputs=stack_outputs,
                  stack_state=stack_state)


def _get_stack_outputs(cfn_client, stack_name):
    stacks = cfn_client.describe_stacks(stack_name)
    if len(stacks) == 1:
        return stacks[0]


def _get_stack_state(cfn_client, stack_name):
    try:
        stack = cfn_client.Stack(stack_name)
    except:
        print('Failed to get stack state.')
        return
    return stack.stack_status


def _json2table(data):
    filter_terms = ['ResponseMetadata']
    table = []
    try:
        for k, v in filter(lambda (k, v): k not in filter_terms, data.iteritems()):
            table.append([k, str(v)])
        return tabulate(table, tablefmt='fancy_grid')
    except Exception:
        return data


def are_credentials_still_valid(boto_session):
    """Check whether the credentials have expired.

    :param boto_session:
    :return: exit_code
    """
    client = boto_session.client('lambda')
    try:
        client.list_functions()
    except Exception as e:
        print(e)
        print(colored.red('Your credentials have expired... Please renew and try again!'))
        return 1
    return 0


def _get_input():
    name = prompt.query('Please enter your Slack API token: ')
    return name


def _get_stack_id(boto_session, stackname):
    client = boto_session.client('cloudformation')
    response = client.describe_stacks(StackName=stackname)
    stack_id = response['Stacks'][0]['StackId']
    return stack_id


def _get_stack_events_last_timestamp(boto_session, stackname):
    '''
    ZERO = timedelta(0)

    class UTC(tzinfo):
        def utcoffset(self, dt):
            return ZERO

        def tzname(self, dt):
            return 'UTC'

        def dst(self, dt):
            return ZERO

    utc = UTC()

    # now_aware = unaware.replace(tzinfo=pytz.UTC)
    # http://stackoverflow.com/questions/5802108/how-to-check-if-a-datetime-object-is-localized-with-pytz
    # d.tzinfo is None or d.tzinfo.utcoffset(d) is None
    #if event['Timestamp'].tzinfo is None or \
    #        event['Timestamp'].tzinfo.utcoffset(event['Timestamp']):
    #    # we have a native timestamp and need to add tzinfo
    #    # most likely this is happening within a test driven by placebo.
    #    event['Timestamp'] = event['Timestamp'].replace(tzinfo=utc)

    # the actual call to AWS has a little headstart
    now = datetime.now(utc) - timedelta(seconds=10)
    return now
    '''

    # we need to get the last event since updatedTime is when the update stated
    client = boto_session.client('cloudformation')
    stack_id = _get_stack_id(boto_session, stackname)
    response = client.describe_stack_events(StackName=stack_id)
    return response['StackEvents'][-1]['Timestamp']


def _poll_stack_events(boto_session, stackname, last_event=None):
    # http://stackoverflow.com/questions/796008/cant-subtract-offset-naive-and-offset-aware-datetimes/25662061#25662061

    finished_statuses = ['CREATE_COMPLETE',
                         'CREATE_FAILED',
                         'DELETE_COMPLETE',
                         'DELETE_FAILED',
                         'ROLLBACK_COMPLETE',
                         'ROLLBACK_FAILED',
                         'UPDATE_COMPLETE',
                         'UPDATE_ROLLBACK_COMPLETE',
                         'UPDATE_ROLLBACK_FAILED']

    failed_statuses = ['CREATE_FAILED',
                       'DELETE_FAILED',
                       'ROLLBACK_COMPLETE',
                       'ROLLBACK_FAILED',
                       'UPDATE_ROLLBACK_COMPLETE',
                       'UPDATE_ROLLBACK_FAILED']

    warning_statuses = ['ROLLBACK_IN_PROGRESS',
                        'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS',
                        'UPDATE_ROLLBACK_IN_PROGRESS']

    success_statuses = ['CREATE_COMPLETE',
                        'DELETE_COMPLETE',
                        'UPDATE_COMPLETE']

    seen_events = []
    # print len(seen_events)
    client = boto_session.client('cloudformation')
    status = ''
    # for the delete command we need the stack_id
    stack_id = _get_stack_id(boto_session, stackname)
    print('%-50s %-25s %-50s %-25s\n' % ('Resource Status', 'Resource ID',
                                         'Reason', 'Timestamp'))
    while status not in finished_statuses:
        response = client.describe_stack_events(StackName=stack_id)
        for event in response['StackEvents'][::-1]:
            if event['EventId'] not in seen_events and \
                    (not last_event or event['Timestamp'] > last_event):
                seen_events.append(event['EventId'])
                resource_status = event['ResourceStatus']
                resource_id = event['LogicalResourceId']
                # this is not always present
                try:
                    reason = event['ResourceStatusReason']
                except KeyError:
                    reason = ''
                timestamp = str(event['Timestamp'])
                message = '%-50s %-25s %-50s %-25s\n' % (resource_status, resource_id,
                                                         reason, timestamp)
                if resource_status in failed_statuses:
                    print(colored.red(message))
                elif resource_status in warning_statuses:
                    print(colored.yellow(message))
                elif resource_status in success_statuses:
                    print(colored.green(message))
                else:
                    print(message)
                if event['LogicalResourceId'] == stackname:
                    status = event['ResourceStatus']
        time.sleep(5)
    exit_code = 0
    if status not in success_statuses:
        exit_code = 1
    return exit_code


def _generate_parameter_entry(conf, raw_param):
    # generate an entry for the parameter list from a raw value read from config
    entry = {
        'ParameterKey': raw_param,
        'ParameterValue': _get_conf_value(conf, raw_param),
        'UsePreviousValue': False
    }
    return entry


def _get_conf_value(conf, raw_param):
    conf_value = conf.get('cloudformation.' + raw_param)
    if isinstance(conf_value, list):
        # if list or array then join to comma separated list
        return ','.join(conf_value)
    else:
        return conf_value


def _generate_parameters(conf):
    # generate the parameter list for the cloudformation template from the
    # conf keys
    raw_parameters = []
    parameter_list = []
    for item in conf.iterkeys():
        for key in conf[item].iterkeys():
            if key not in ['StackName', 'TemplateBody', 'ArtifactBucket']:
                raw_parameters.append(key)
    for param in raw_parameters:
        entry = _generate_parameter_entry(conf, param)
        parameter_list.append(entry)

    return parameter_list


def _stack_exists(boto_session, stackName):
    client = boto_session.client('cloudformation')
    try:
        response = client.describe_stacks(
            StackName=stackName
        )
    except Exception:
        return False
    else:
        return True


def deploy_stack(boto_session, conf, cloudformation, slack_token=None,
                 slack_channel='systemmessages', override_stack_policy=False):
    """Deploy the stack to AWS cloud. Does either create or update the stack.

    :param conf:
    :param slack_token:
    :param slack_channel:
    :param override_stack_policy:
    :return: exit_code
    """
    stackname = _get_stack_name(conf)
    parameters = _generate_parameters(conf)
    _call_hook(boto_session, conf, stackname, parameters, cloudformation,
               hook='pre_hook')
    if _stack_exists(boto_session, stackname):
        exit_code = _update_stack(boto_session, conf, cloudformation,
                                  parameters, override_stack_policy,
                                  slack_token, slack_channel)
    else:
        exit_code = _create_stack(boto_session, conf, cloudformation,
                                  parameters, slack_token, slack_channel)
    _call_hook(boto_session, conf, stackname, parameters, cloudformation,
               hook='post_hook',
               message='CloudFormation is done, now executing post hook...')
    return exit_code


def _s3_upload(boto_session, conf, cloudformation):
    region = boto_session.region_name
    resource_s3 = boto_session.resource('s3')
    bucket = _get_artifact_bucket(conf)
    dest_key = 'kumo/%s/%s-cloudformation.json' % (region, _get_stack_name(conf))

    source_file = generate_template_file(conf, cloudformation)

    s3obj = resource_s3.Object(bucket, dest_key)
    s3obj.upload_file(source_file)
    s3obj.wait_until_exists()

    s3url = 'https://s3-%s.amazonaws.com/%s/%s' % (region, bucket, dest_key)

    return s3url


def _get_stack_policy(cloudformation):
    default_stack_policy = json.dumps({
        'Statement': [
            {
                'Effect': 'Allow',
                'Action': 'Update:Modify',
                'Principal': '*',
                'Resource': '*'
            },
            {
                'Effect': 'Deny',
                'Action': ['Update:Replace', 'Update:Delete'],
                'Principal': '*',
                'Resource': '*'
            }
        ]
    })

    stack_policy = default_stack_policy

    # check if a user specified his own stack policy
    # if CLOUDFORMATION_FOUND:
    if 'get_stack_policy' in dir(cloudformation):
        stack_policy = cloudformation.get_stack_policy()
        print(colored.magenta('Applying custom stack policy'))

    return stack_policy


def _get_stack_policy_during_update(cloudformation, override_stack_policy):
    if override_stack_policy:
        default_stack_policy_during_update = json.dumps({
            'Statement': [
                {
                    'Effect': 'Allow',
                    'Action': 'Update:*',
                    'Principal': '*',
                    'Resource': '*'
                }
            ]
        })
    else:
        default_stack_policy_during_update = json.dumps({
            'Statement': [
                {
                    'Effect': 'Allow',
                    'Action': 'Update:Modify',
                    'Principal': '*',
                    'Resource': '*'
                },
                {
                    'Effect': 'Deny',
                    'Action': ['Update:Replace', 'Update:Delete'],
                    'Principal': '*',
                    'Resource': '*'
                }
            ]
        })

    stack_policy_during_update = default_stack_policy_during_update

    # check if a user specified his own stack policy
    # if CLOUDFORMATION_FOUND:
    if 'get_stack_policy_during_update' in dir(cloudformation):
        stack_policy_during_update = cloudformation.get_stack_policy_during_update()
        print(colored.magenta('Applying custom stack policy for updates\n'))

    return stack_policy_during_update


def _create_stack(boto_session, conf, cloudformation, parameters,
                  slack_token=None, slack_channel='systemmessages'):
    # create stack with all the information we have
    client_cf = boto_session.client('cloudformation')
    stackname = _get_stack_name(conf)
    _call_hook(boto_session, conf, stackname, parameters, cloudformation,
               hook='pre_create_hook')
    try:
        _get_artifact_bucket(conf)
        response = client_cf.create_stack(
            StackName=_get_stack_name(conf),
            TemplateURL=_s3_upload(boto_session, conf, cloudformation),
            Parameters=parameters,
            Capabilities=[
                'CAPABILITY_IAM',
            ],
            StackPolicyBody=_get_stack_policy(cloudformation),
        )
    # if we have no artifacts bucket configured then upload the template directly
    except ConfigMissingException:
        response = client_cf.create_stack(
            StackName=_get_stack_name(conf),
            TemplateBody=cloudformation.generate_template(),
            Parameters=parameters,
            Capabilities=[
                'CAPABILITY_IAM',
            ],
            StackPolicyBody=_get_stack_policy(cloudformation),
        )

    message = 'kumo bot: created stack %s ' % _get_stack_name(conf)
    monitoring.slack_notification(slack_channel, message, slack_token)
    # create means no last_event!
    exit_code = _poll_stack_events(boto_session, stackname)
    _call_hook(boto_session, conf, stackname, parameters, cloudformation,
               hook='post_create_hook',
               message='CloudFormation is done, now executing post create hook...')
    return exit_code


def _update_stack(boto_session, conf, cloudformation, parameters,
                  override_stack_policy, slack_token=None,
                  slack_channel='systemmessages'):
    # update stack with all the information we have
    exit_code = 0
    client_cf = boto_session.client('cloudformation')
    stackname = _get_stack_name(conf)
    last_event = _get_stack_events_last_timestamp(boto_session, stackname)
    try:
        stackname = _get_stack_name(conf)
        _call_hook(boto_session, conf, stackname, parameters, cloudformation,
                   hook='pre_update_hook')
        try:
            _get_artifact_bucket(conf)
            response = client_cf.update_stack(
                StackName=_get_stack_name(conf),
                TemplateURL=_s3_upload(boto_session, conf, cloudformation),
                Parameters=parameters,
                Capabilities=[
                    'CAPABILITY_IAM',
                ],
                StackPolicyBody=_get_stack_policy(cloudformation),
                StackPolicyDuringUpdateBody=_get_stack_policy_during_update(
                    cloudformation,
                    override_stack_policy)

            )
        except ConfigMissingException:
            response = client_cf.update_stack(
                StackName=_get_stack_name(conf),
                TemplateBody=cloudformation.generate_template(),
                Parameters=_generate_parameters(conf),
                Capabilities=[
                    'CAPABILITY_IAM',
                ],
                StackPolicyBody=_get_stack_policy(cloudformation),
                StackPolicyDuringUpdateBody=_get_stack_policy_during_update(
                    cloudformation,
                    override_stack_policy)
            )

        message = 'kumo bot: updated stack %s ' % _get_stack_name(conf)
        monitoring.slack_notification(slack_channel, message, slack_token)
        exit_code = _poll_stack_events(boto_session, stackname)
        _call_hook(boto_session, conf, stackname, parameters, cloudformation,
                   hook='post_update_hook',
                   message='CloudFormation is done, now executing post update hook...')
    except Exception as e:
        if 'No updates' in repr(e):
            print(colored.yellow('No updates are to be performed.'))
        else:
            print(type(e))
            print(colored.red('Exception occurred during update:' + str(e)))

    return exit_code


def delete_stack(boto_session, conf, slack_token=None,
                 slack_channel='systemmessages'):
    """Delete the stack from AWS cloud.

    :param boto_session:
    :param conf:
    :param slack_token:
    :param slack_channel:
    """
    client_cf = boto_session.client('cloudformation')
    response = client_cf.delete_stack(
        StackName=_get_stack_name(conf),
    )
    message = 'kumo bot: deleted stack %s ' % _get_stack_name(conf)
    monitoring.slack_notification(slack_channel, message, slack_token)
    stackname = _get_stack_name(conf)
    return _poll_stack_events(boto_session, stackname)


def list_stacks(boto_session, out=sys.stdout):
    """Print out the list of stacks deployed at AWS cloud.

    :param boto_session:
    :return:
    """
    client_cf = boto_session.client('cloudformation')
    response = client_cf.list_stacks(
        StackStatusFilter=[
            'CREATE_IN_PROGRESS', 'CREATE_COMPLETE', 'ROLLBACK_IN_PROGRESS',
            'ROLLBACK_COMPLETE', 'DELETE_IN_PROGRESS', 'DELETE_FAILED',
            'UPDATE_IN_PROGRESS', 'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS',
            'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_IN_PROGRESS',
            'UPDATE_ROLLBACK_FAILED', 'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS',
            'UPDATE_ROLLBACK_COMPLETE',
        ]
    )
    result = {}
    stack_sum = 0
    for summary in response['StackSummaries']:
        result['StackName'] = summary["StackName"]
        result['CreationTime'] = summary['CreationTime']
        result['StackStatus'] = summary['StackStatus']
        print(_json2table(result), file=out)
        stack_sum += 1
    print('listed %s stacks' % str(stack_sum), file=out)


def create_change_set(boto_session, conf, cloudformation):
    client = boto_session.client('cloudformation')
    change_set_name = ''.join(random.SystemRandom().choice(
        string.ascii_uppercase) for _ in range(8))
    response = client.create_change_set(
        StackName=_get_stack_name(conf),
        TemplateBody=cloudformation.generate_template(),
        Parameters=_generate_parameters(conf),
        Capabilities=[
            'CAPABILITY_IAM',
        ],
        ChangeSetName=change_set_name
    )
    # print json2table(response)
    return change_set_name, _get_stack_name(conf)


def describe_change_set(boto_session, change_set_name, stack_name):
    """Print out the change_set to console.
    This needs to run create_change_set first.

    :param boto_session:
    :param change_set_name:
    :param stack_name:
    """
    client = boto_session.client('cloudformation')

    status = None
    while status not in ['CREATE_COMPLETE', 'FAILED']:
        response = client.describe_change_set(
            ChangeSetName=change_set_name,
            StackName=stack_name)
        status = response['Status']
        print('##### %s' % status)
        if status == 'CREATE_COMPLETE':
            for change in response['Changes']:
                print(_json2table(change['ResourceChange']))


def _get_stack_name(conf):
    return conf.get('cloudformation.StackName')


def _get_artifact_bucket(conf):
    return conf.get('cloudformation.artifactBucket')


def generate_template_file(conf, cloudformation):
    """Writes the template to disk
    """
    template_body = cloudformation.generate_template()
    template_file_name = _get_stack_name(conf) + '-generated-cf-template.json'
    with open(template_file_name, 'w') as opened_file:
        opened_file.write(template_body)
    print('wrote cf-template for %s to disk: %s' % (get_env(), template_file_name))
    return template_file_name
