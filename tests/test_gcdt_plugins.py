# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

import mock

from gcdt.gcdt_plugins import load_plugins


def test_load_plugins():
    ep = mock.Mock(spec=['load'])
    plugin = mock.Mock(spec=['register'])
    ep.load.return_value = plugin

    with mock.patch('pkg_resources.iter_entry_points', return_value=[ep]):
        load_plugins()
        ep.load.assert_called_once()
        plugin.register.assert_called_once()
