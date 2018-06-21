#!/usr/bin/env python2.7

from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import argparse
import sys

from schdl import app
from schdl import mongo
from schdl import util


def main(args):
    parser = argparse.ArgumentParser(description='Add a user.')
    parser.add_argument('--school', required=True)
    parser.add_argument('--email', required=True, action='append')
    parser.add_argument('--first')
    parser.add_argument('--middle')
    parser.add_argument('--last')
    parser.add_argument('--password')
    parser.add_argument('--passhash')
    parser.add_argument('--role', default=[], action='append')
    args = parser.parse_args(args)
    school = app.mongo.db.schools.find_one({'fragment': args.school})
    if not school:
        sys.stderr.write('School %s does not exist.\n' % args.school)
        sys.exit(1)
    user = util.User({
        'email': args.email,
        'first': args.first,
        'middle': args.middle,
        'last': args.last,
        'schedules': [],
        'secret': util.generate_secret(),
        'roles': args.role,
    }, school)
    if args.password and not args.passhash:
        user.set_password(args.password)
    elif args.passhash:
        user['passhash'] = args.passhash
    else:
        sys.stderr.write(
            'Exactly one of --passhash, --password must be provided.\n')
        sys.exit(1)
    c = mongo.SchoolCollections(school['fragment'])
    c.user.insert(user.user)

if __name__ == '__main__':
    with app.test_request_context('/'):
        main(sys.argv[1:])
