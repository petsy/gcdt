#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The 'gcdt' tool provides 'common' administration tasks.
"""

from __future__ import print_function
import sys
from docopt import docopt
from gcdt.utils import configure, version, get_command

# creating docopt parameters and usage help
DOC = ''''Usage:
        gcdt configure
        gcdt version

-h --help           show this
'''


def main():
    arguments = docopt(DOC)

    # Run command
    if arguments['configure']:
        configure()
    elif arguments['version']:
        version()

    sys.exit(0)


if __name__ == '__main__':
    main()
