#!/usr/bin/env python2.7

from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import logging

from schdl.wsgi import app


def main():
    logging.basicConfig(level=logging.INFO)
    app.run()


if __name__ == '__main__':
    main()
