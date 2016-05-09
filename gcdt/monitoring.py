from time import time
from functools import wraps
import boto3
import datetime
import json
from logger import log_json, setup_logger
from slacker import Slacker

log = setup_logger(logger_name="monitoring")


def get_cloudwatch_client():
    return boto3.client("cloudwatch")


def get_cloudwatch_events_client():
    return boto3.client('events')


def put_metrics(Namespace, MetricData):
    cloudwatch = get_cloudwatch_client()
    cloudwatch.put_metric_data(Namespace=Namespace, MetricData=MetricData)


def timing(namespace, metric, value):
    """
    Record a timing.
    >>> monitoring.timing("query.response.time", 1234)
    """
    print(metric, 'ms', value)
    put_metrics(
        Namespace=namespace,
        MetricData=[
            {'MetricName': metric,
             'Value': value, 'Unit': 'Seconds'}
        ],
    )


def timed(namespace, metric):
    """
    A decorator that will measure the distribution of a function's run
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
            timing(namespace, metric, time() - start)
            return result

        return wrapped

    return wrapper


def push_event(namespace, event):
    client = get_cloudwatch_events_client()
    detail = {"description": event}
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
    log.info(namespace + " " + event)
    log.info(("pushed cloudwatch event: %s" % response))
    print response


def event(namespace, event):
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
            push_event(namespace, event)
            return result

        return wrapped

    return wrapper


def send_to_slacker(channel, event, slack_token):
    if slack_token:
        slack = Slacker(slack_token)

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
                slack.chat.post_message('#' + channel, event)
                return result

            return wrapped

        return wrapper
    else:
        pass


def slacker_notifcation(channel, message, slack_token):
    slack = Slacker(slack_token)
    slack.chat.post_message('#' + channel, message)
