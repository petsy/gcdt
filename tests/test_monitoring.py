# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
from StringIO import StringIO

from nose.tools import assert_true, assert_regexp_matches, assert_equal, \
    assert_items_equal
import nose

from gcdt.monitoring import datadog_notification, \
    _datadog_get_tags, datadog_error
#from gcdt.utils import read_gcdt_user_config, get_context


def test_datadog_get_tags():
    context = {'a': '1', 'b': '2', '_c': '3'}
    actual = _datadog_get_tags(context)
    assert_items_equal(actual, ['a:1', 'b:2'])


'''
def test_datadog_notification():
    socket = datadog.statsd.socket = FakeSocket()
    metric = 'gcdt.kumo.deploy'
    tags = ['env:dev', 'stack_name:gcdt-supercars-dev']

    datadog_notification(metric, tags)
    assert_equal(socket.recv(),
                 'gcdt.kumo.deploy:1|c|#env:dev,stack_name:gcdt-supercars-dev')
'''

'''
# TODO: how to test this without creating 'additional' entries in datadog
def test_datadog_notification():
    context = get_context('yugen', 'deploy')
    datadog_notification(context)


def test_datadog_error():
    context = get_context('yugen', 'deploy')
    datadog_error(context, 'message')
'''
