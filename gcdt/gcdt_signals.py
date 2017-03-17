# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
from blinker import signal

# lifecycle implementation adapted from
# https://github.com/finklabs/aws-deploy/blob/master/aws_deploy/signals.py
# we use signals here for testability and better composition of code
# the signals provide hooks to add components into the tool lifecycle

# run-level signals:


initialized = signal('initialized')  # after reading arguments and context

config_read_init = signal('config_read_init')
config_read_finalized = signal('config_read_finalized')

lookup_init = signal('lookup_init')
lookup_finalized = signal('lookup_finalized')

config_validation_init = signal('config_validation_init')
config_validation_finalized = signal('config_validation_finalized')

bundle_pre = signal('bundle_pre')  # we need this signal to implement the prebundle-hook
bundle_init = signal('bundle_init')
bundle_finalized = signal('bundle_finalized')

command_init = signal('command_init')
command_finalized = signal('command_finalized')

error = signal('error')

finalized = signal('finalized')  # right before exit
