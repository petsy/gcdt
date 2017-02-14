#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The 'gcdt' tool provides 'common' administration tasks.
"""
from __future__ import unicode_literals, print_function
import sys

from . import utils
from . import gcdt_lifecycle
from .gcdt_cmd_dispatcher import cmd


# creating docopt parameters and usage help
# we do not need the configure any more!
#        gcdt configure
#        gcdt version
#
#-h --help           show this
DOC = ''''Usage:
        gcdt version

-h --help           show this
'''


@cmd(spec=['version'])
def version_cmd():
    utils.version()


def main():
    sys.exit(gcdt_lifecycle.main(DOC, 'gcdt'))


if __name__ == '__main__':
    main()
