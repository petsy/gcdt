# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import pkg_resources
import logging


log = logging.getLogger(__name__)


# TODO we have all plugins in one single repo so we need a mechanism to filter
# the ones we want to use!


def check_hook_mechanism_is_intact(plugin):
    """Check if the hook configuration adheres to minimal standards.

    :param plugin:
    :return: True if valid plugin / module.
    """
    if not hasattr(plugin, 'register'):
        return False
    if not hasattr(plugin, 'deregister'):
        return False
    return True


def load_plugins(group='gcdt10'):
    """Load and register installed gcdt plugins.
    """
    # on using entrypoints:
    # http://stackoverflow.com/questions/774824/explain-python-entry-points
    # TODO: make sure we do not have conflicting generators installed!
    for ep in pkg_resources.iter_entry_points(group, name=None):
        plugin = ep.load()  # load the plugin
        if check_hook_mechanism_is_intact(plugin):
            plugin.register()   # register the plugin so it listens to gcdt_signals
        else:
            log.warning('No valid hook configuration: %s. Not using hooks!', plugin)
