#!/usr/bin/env python2.7

from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import argparse
import sys
import logging

from schdl import app
from schdl import mongo
from schdl import updates

LOGGER = logging.getLogger(__name__)


def main(args):
    parser = argparse.ArgumentParser(description='Process one update.')
    parser.add_argument('--school', required=True)
    parser.add_argument('--update_file', type=file)
    args = parser.parse_args(args)
    logging.basicConfig(level=logging.INFO)
    schools = app.mongo.db.schools
    school = schools.find_one({'fragment': args.school})
    if not school:
        print('School %s not found' % args.school)
        sys.exit(1)

    c = mongo.SchoolCollections(args.school)

    if args.update_file:
        LOGGER.info('Loading update for %s from %s',
                    school['name'], args.update_file.name)
        updates.add_update(school, args.update_file, c)
    results = updates.process_update(school, c)
    if results is not None:
        print('%s new, %s updates, %s same, %s deletes'
              % results)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    with app.test_request_context('/'):
        main(sys.argv[1:])
