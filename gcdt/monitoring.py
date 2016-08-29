# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
from clint.textui import colored
from slacker import Slacker
from gcdt.logger import setup_logger

log = setup_logger(__name__)


''' currently not used?
def _put_metrics(namespace, metric_data):
    cloudwatch = boto3.client("cloudwatch")
    cloudwatch.put_metric_data(Namespace=namespace, MetricData=metric_data)


def _timing(namespace, metric, value):
    """Record a timing.

    monitoring.timing("query.response.time", 1234)
    """
    print(metric, 'ms', value)
    _put_metrics(
        Namespace=namespace,
        MetricData=[
            {'MetricName': metric,
             'Value': value, 'Unit': 'Seconds'}
        ],
    )


def timed(namespace, metric):
    """A decorator that will measure the distribution of a function's execution
    time.
    ::
        @monitoring.timed('user.query.time')
        def get_user(user_id):
            # Do what you need to ...
            pass
        # Is equivalent to ...
        start = time.time()
        try:
            get_user(user_id)
        finally:
            monitoring.timing('user.query.time', time.time() - start)
    """
    def wrapper(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            start = time()
            result = func(*args, **kwargs)
            _timing(namespace, metric, time() - start)
            return result

        return wrapped

    return wrapper
'''


''' currently not used?
def _push_event(namespace, cloudwatch_event):
    client = boto3.client('events')
    detail = {"description": cloudwatch_event}
    response = client.put_events(
        Entries=[
            {
                'Time': datetime.datetime.now(),
                'Source': namespace,
                'Resources': [],
                'DetailType': 'not used',
                'Detail': json.dumps(detail)
            },
        ]
    )
    log.info(namespace + " " + cloudwatch_event)
    log.info(("pushed cloudwatch event: %s" % response))
    print response


def event(namespace, cloudwatch_event):
    """
    A decorator that will push a custom cloudwatch event
    ::
        @monitoring.event('deploytool', 'deployed xyz')
        def deploy_something():
            # Do what you need to ...
            pass

    """
    def wrapper(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            result = func(*args, **kwargs)
            _push_event(namespace, cloudwatch_event)
            return result

        return wrapped

    return wrapper
'''

''' currently not used?
def send_to_slack(channel, cloudwatch_event, slack_token):
    """A decorator that will push a custom cloudwatch event

    @monitoring.event('deploytool', 'deployed xyz')
    def deploy_something():
        # Do what you need to ...
        pass
    """
    if slack_token:
        slack = Slacker(slack_token)

        def wrapper(func):
            @wraps(func)
            def wrapped(*args, **kwargs):
                result = func(*args, **kwargs)
                slack.chat.post_message('#%s' % channel, cloudwatch_event)
                return result

            return wrapped

        return wrapper
'''


# TODO: maybe move to utils?
def slack_notification(channel, message, slack_token, out=sys.stdout):
    if channel and slack_token:
        try:
            slack = Slacker(slack_token)
            slack.chat.post_message('#%s' % channel, message)
        except Exception as e:
            print(colored.red('We can not use your slack token: %s' % str(e)),
                  file=out)
