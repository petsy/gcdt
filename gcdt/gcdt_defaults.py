# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

"""This file contains configuration for gcdt tools so we do not need
hardcoded values.
"""

# basic structure:
'''
{
    'kumo': {},
    'tenkai': {},
    'ramuda': {},
    'yugen': {},
    'plugins': {
        '<plugin_name>': {}
    }
}
'''


DEFAULT_CONFIG = {
    'ramuda': {
        'settings_file': 'settings.json'
    }
}
