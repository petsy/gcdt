# -*- coding: utf-8 -*-
import os
import json
from StringIO import StringIO
from nose.tools import assert_equal
import nose
from gcdt.kumo_viz import cfn_viz


def here(p): return os.path.join(os.path.dirname(__file__), p)


def test_cfn_viz():
    template_path = here(
        'resources/sample_kumo_viz/ELBStickinessSample.template')
    dot_path = here(
        'resources/sample_kumo_viz/expected.dot')

    with open(template_path, 'r') as tfile:
        template = json.loads(tfile.read())

    out = StringIO()
    cfn_viz(template, parameters={'KeyName': 'abc123'}, out=out)

    with open(dot_path, 'r') as dfile:
        expected_dot = dfile.read()

    assert_equal(str(out.getvalue()), expected_dot)
