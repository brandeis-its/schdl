#!/usr/bin/env python2.7

from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import argparse
import sys

from schdl import app
from schdl import mongo


def main(args):
    parser = argparse.ArgumentParser(description='Add a school.')
    parser.add_argument('--fragment', required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--email_domain', required=True)
    parser.add_argument('--website', required=True)
    parser.add_argument('--hostname', required=True, action='append')
    args = parser.parse_args(args)
    school = {
        'fragment': args.fragment,
        'name': args.name,
        'email_domain': args.email_domain,
        'website': args.website,
        'hostname': args.hostname,
        'failure_emails': [args.fragment + '-update-failures@schdl.net'],
    }
    app.mongo.db.schools.insert(school)
    mongo.EnsureIndices(shared=False, school_fragment=args.fragment)

if __name__ == '__main__':
    with app.test_request_context('/'):
        main(sys.argv[1:])
