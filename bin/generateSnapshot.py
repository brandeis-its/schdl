#!/usr/bin/env python2.7

from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import sys

from schdl import app
from schdl import mongo
from schdl import snapshot


def main(school):
    c = mongo.SchoolCollections(school)
    snapshot.generate_snapshot(c, sys.stdout)

if __name__ == '__main__':
    with app.test_request_context('/'):
        main(*sys.argv[1:])
