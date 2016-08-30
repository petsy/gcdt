# -*- coding: utf-8 -*-
from nose.tools import assert_equal,assert_dict_contains_subset,assert_in
import nose
from nose.plugins.attrib import attr
from gcdt.utils import get_context


@attr('aws')
def test_get_context():
    actual = get_context('kumo', 'deploy')
    expected_subset = {
        'tool': 'kumo',
        'command': 'deploy',
        'env': 'dev',
    }
    assert_dict_contains_subset(expected_subset, actual)
    assert_in('_datadog_api_key', actual)
    assert_in('user', actual)
    assert_in('version', actual)
