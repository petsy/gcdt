# -*- coding: utf-8 -*-
from __future__ import print_function
import os

from .helpers_aws import recorder, file_reader, boto_session, here
from .helpers import temp_folder
from . import helpers


def test_recorder(temp_folder):
    c = {'x': 100}

    def fake_func():
        c['x'] += 1
        return c['x']

    wrapped = recorder(temp_folder[0], fake_func)
    wrapped()
    wrapped()
    with open(os.path.join(temp_folder[0], 'fake_func'), 'r') as rfile:
        body = ''.join(rfile.readlines())
        assert body == '101\n102\n'


def test_file_reader(temp_folder):
    filename = os.path.join(temp_folder[0], 'fake_data_file')
    with open(filename, 'w') as dfile:
        print('111', file=dfile)
        print('222', file=dfile)

    with open(filename, 'r') as dfile:
        reader = file_reader(temp_folder[0], 'fake_data_file')
        assert reader() == '111'
        assert reader() == '222'


def test_random_string_recording(boto_session):
    # record and playback cases are identical for this test
    lines = []
    for i in range(5):
        lines.append(helpers.random_string())

    prefix = 'tests.test_helpers_aws.test_random_string_recording'
    record_dir = os.path.join(here('./resources/placebo'), prefix)
    random_string_filename = 'random_string.txt'
    with open(os.path.join(record_dir, random_string_filename), 'r') as rfile:
        rlines = [l.strip() for l in rfile.readlines()]

        assert lines == rlines
