#!/usr/bin/env python2.7

from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import logging

from brandeis.redirect import app


def main():
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True, port=5001)


if __name__ == '__main__':
    main()
