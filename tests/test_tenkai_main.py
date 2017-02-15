# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import os

import pytest

from gcdt.tenkai_main import version_cmd, deploy_cmd, bundle_cmd

from .helpers_aws import check_preconditions, get_tooldata
from .helpers_aws import awsclient  # fixtures !
from .test_tenkai_aws import sample_codedeploy_app  # fixtures !
from . import here


# note: xzy_main tests have a more "integrative" character so focus is to make
# sure that the gcdt parts fit together not functional coverage of the parts.


@pytest.fixture(scope='function')  # 'function' or 'module'
def simple_codedeploy_folder():
    # helper to get into the sample folder so kumo can find cloudformation.py
    cwd = (os.getcwd())
    os.chdir(here('./resources/simple_codedeploy/'))
    yield
    # cleanup
    os.chdir(cwd)  # cd back to original folder


@pytest.fixture(scope='function')  # 'function' or 'module'
def sample_codedeploy_app_working_folder():
    # helper to get into the sample folder so kumo can find cloudformation.py
    cwd = (os.getcwd())
    os.chdir(here('./resources/sample_codedeploy_app/working/'))
    yield
    # cleanup
    os.chdir(cwd)  # cd back to original folder


def test_version_cmd(capsys):
    version_cmd()
    out, err = capsys.readouterr()
    assert out.startswith('gcdt version')


@pytest.mark.aws
@check_preconditions
def test_deploy_cmd(awsclient, sample_codedeploy_app,
                    sample_codedeploy_app_working_folder):
    tooldata = get_tooldata(awsclient, 'tenkai', 'deploy')
    deploy_cmd(**tooldata)


def test_bundle_cmd(simple_codedeploy_folder):
    tooldata = get_tooldata(None, 'tenkai', 'bundle')
    bundle_cmd(**tooldata)
    filename = '%s/tenkai-bundle%s.tar.gz' % ('/tmp', os.getenv('BUILD_TAG', ''))
    assert os.path.exists(filename)
    os.unlink(filename)
