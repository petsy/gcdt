# -*- coding: utf-8 -*-
from StringIO import StringIO
from nose.tools import assert_true, assert_regexp_matches, assert_equal
from gcdt.monitoring import slack_notification
from gcdt.utils import read_gcdt_user_config


def test_slack_notification():
    # read token from ~/.gcdt file
    slack_token, _ = read_gcdt_user_config()
    channel = 'test_do_not_join'
    message = 'testing gcdt and tools...'
    out = StringIO()

    slack_notification(channel, message, slack_token, out)

    assert_equal(out.getvalue().strip(), '')


def test_slack_notification_invalid_token():
    # invalid token
    slack_token = 'xoxp-12345678901-12345678901-12345678901-4e6es20339'
    channel = 'test_do_not_join'
    message = 'testing gcdt...'
    out = StringIO()

    slack_notification(channel, message, slack_token, out)

    assert_regexp_matches(out.getvalue().strip(),
                          'We can not use your slack token: invalid_auth')
