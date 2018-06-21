#!/usr/bin/env python2.7

from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import argparse
import itertools
import sys

from schdl import app
from schdl import mongo

def main(args):
    parser = argparse.ArgumentParser(description='Dump recommender data.')
    parser.add_argument('--school', required=True)
    args = parser.parse_args(args)
    schools = app.mongo.db.schools
    school = schools.find_one({'fragment': args.school})
    if not school:
        print('School %s not found' % args.school)
        sys.exit(1)

    c = mongo.SchoolCollections(args.school)
    sections = c.course.aggregate([
        {'$project': {'continuity_id': 1, 'section_id': '$sections.id', '_id': 0}},
        {'$unwind': '$section_id'},
        {'$sort': {'continuity_id': 1}},
    ])['result']
    continuity_ids = {s['section_id']: s['continuity_id'] for s in sections}
    user_sections = c.user.aggregate([
        {'$project': {'schedules.sections.id': 1, 'schedules.sections.status': 1}},
        {'$unwind': '$schedules'},
        {'$unwind': '$schedules.sections'},
        {'$match': {'schedules.sections.status': {'$ne': 'no'}}},
        {'$project': {'section': '$schedules.sections.id'}},
        {'$sort': {'_id': 1}},
    ])['result']
    sys.stdout.write('User\tCourse\n')
    for u, (_, sections) in enumerate(itertools.groupby(user_sections, lambda x: x['_id'])):
        # TODO: convert u to hex or base64 to minimize size
        for section in sections:
            c_id = continuity_ids[section['section']]
            if c_id:
                sys.stdout.write('{}\t{}\n'.format(u, c_id))
    

if __name__ == '__main__':
    with app.test_request_context('/'):
        main(sys.argv[1:])
