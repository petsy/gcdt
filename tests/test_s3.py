# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import logging

import pytest

from gcdt.s3 import bucket_exists, upload_file_to_s3, ls

from .helpers_aws import awsclient, temp_bucket  # fixtures!
from .helpers import random_file  # fixtures!
from . import helpers

log = logging.getLogger(__name__)


def test_bucket_exists(awsclient, temp_bucket):
    assert bucket_exists(awsclient, temp_bucket)


def test_bucket_does_not_exist(awsclient):
    temp_string = helpers.random_string()
    bucket_name = 'unittest-lambda-s3-event-source-%s' % temp_string
    assert not bucket_exists(awsclient, bucket_name)


def test_upload_file_to_s3(awsclient, temp_bucket, random_file):
    upload_file_to_s3(awsclient, temp_bucket, 'content.txt', random_file)
    assert 'content.txt' in ls(awsclient, temp_bucket)
