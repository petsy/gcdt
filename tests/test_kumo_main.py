# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

import pytest
import regex

from gcdt.kumo_main import version_cmd
from gcdt import __version__
from gcdt.kumo_core import list_stacks

from .helpers_aws import check_preconditions
from .helpers_aws import awsclient  # fixtures!

# note: xzy_main tests have a more "integrative" character so focus is to make
# sure that the gcdt parts fit together not functional coverage of the parts.


def test_version_cmd(capsys):
    version_cmd()
    out, err = capsys.readouterr()
    assert out.startswith('gcdt version')


def get_context(awsclient, tool, command):
    return {
        'tool': tool,
        'command': command,
        'version': __version__,
        'user': 'unittest',
        'awsclient': awsclient
    }


@pytest.mark.aws
@check_preconditions
def test_list_stacks(awsclient, capsys):
    #context = get_context(awsclient, 'kumo', 'list')
    list_stacks(awsclient)
    out, err = capsys.readouterr()
    # using regular expression search in captured output
    assert regex.search('listed \d+ stacks', out) is not None
