#!/usr/bin/env python2.7

from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import shutil
import sys

from schdl import app
from schdl import mongo
from schdl import updates


def main(school_fragment):
    school = app.mongo.db.schools.find_one_or_404(
        {'fragment': school_fragment},
        {'_id': False})
    c = mongo.SchoolCollections(school_fragment)
    snapshot = updates.get_latest_snapshot(school, c, {'_id': 'fake id'})
    shutil.copyfileobj(snapshot, sys.stdout)

if __name__ == '__main__':
    with app.test_request_context('/'):
        main(*sys.argv[1:])
