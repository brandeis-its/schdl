#!/usr/bin/env python2.7

from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import argparse
import sys

from schdl import app
from schdl import util


def main(args):
    parser = argparse.ArgumentParser(description='Set a school\'s API key.')
    parser.add_argument('--school', required=True)
    args = parser.parse_args(args)
    school = app.mongo.db.schools.find_one({'fragment': args.school})
    if school is None:
        sys.stderr.write('School "%s" not found!\n' % args.school)
        sys.exit(1)
    api_key = util.generate_secret()
    if sys.stdout.isatty():
        sys.stdout.write('API key for %s is "%s"\n'
                         % (school['name'], api_key))
    else:
        sys.stdout.write(api_key)
    app.mongo.db.schools.update(
        {'_id': school['_id']},
        {
            '$set': {
                'api_key_hash': app.bcrypt.generate_password_hash(api_key),
            }
        }
    )

if __name__ == '__main__':
    with app.test_request_context('/'):
        main(sys.argv[1:])
