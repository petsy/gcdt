# -*- coding: utf-8 -*-
import pytest

from gcdt.config_reader import _get_secret

from .helpers_aws import awsclient


# TODO fix recording (decoding) for skiped tests
@pytest.mark.aws
@pytest.mark.skip
def test_get_secret(awsclient):
    actual = _get_secret(awsclient, 'test-secret')
    assert actual == 'geheim'

@pytest.mark.aws
@pytest.mark.skip
def test_get_secret_with_version(awsclient):
    # not used in gcdt but implemented in get_secret!
    actual = _get_secret(awsclient, 'test-secret', version='0000000000000000001')
    assert actual == 'geheim'
