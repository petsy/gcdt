# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import pytest

from gcdt.config_reader import get_secret

from .helpers_aws import awsclient  # fixture!


# TODO fix recording (decoding) for skipped tests
@pytest.mark.skip
@pytest.mark.aws
def test_get_secret(awsclient):
    actual = get_secret(awsclient, 'test-secret')
    assert actual == 'geheim'
    assert False


@pytest.mark.skip
@pytest.mark.aws
def test_get_secret_with_version(awsclient):
    # not used in gcdt but implemented in get_secret!
    actual = get_secret(awsclient, 'test-secret', version='0000000000000000001')
    assert actual == 'geheim'
