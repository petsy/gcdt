# -*- coding: utf-8 -*-
from nose.tools import assert_dict_contains_subset,assert_in
import pytest

from gcdt.utils import get_context


@pytest.mark.aws
def test_get_context():
    actual = get_context('kumo', 'deploy')
    expected_subset = {
        'tool': 'kumo',
        'command': 'deploy',
        'env': 'dev',
    }
    assert_dict_contains_subset(expected_subset, actual)
    # the api_key is currently not rolled out see OPS-126
    # assert_in('_datadog_api_key', actual)
    assert_in('user', actual)
    assert_in('version', actual)
