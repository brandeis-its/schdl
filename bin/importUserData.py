#!/usr/bin/env python2.7

from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import datetime
import json
import logging
import sys

from schdl import app
from schdl import mongo
from schdl import util


LOGGER = logging.getLogger(__name__)


def find_section(term, sect, c):
    sid = sect['section_id'] + '-' + sect['section']
    course = c.section.find_one({
        'sections.id': sid,
        'term': term,
    }, {'_id': True, 'sections.$': True})
    if course:
        return course['sections'][0]['id']
    else:
        raise ValueError('Can\'t find section term=%s, id=%s, data=%s'
                         % (term, sid, sect))


def main(args):
    c = mongo.SchoolCollections('brandeis')
    for i, line in enumerate(sys.stdin, 1):
        try:
            data = json.loads(line)
            user = {
                'first': data['first'],
                'middle': data['middle'],
                'last': data['last'],
                'passhash': data['passhash'],
                'email': [data['email']] + data['additional_emails'],
                'schedules': [],
                'roles': [],
            }
            # TODO(eitan): set user['_id'] using created date
            # bson.objectid.ObjectId.from_datetime(
            #     datetime.datetime.strptime(
            #         data['created'],
            #         '%Y-%m-%d' %H:%M:%S'))
            # then fix for uniqueness
            user['secret'] = data.get('sharing_key')
            if not user['secret']:
                user['secret'] = util.generate_secret()
            for sch in data['schedules']:
                term = sch['id']
                if term < '1071':
                    LOGGER.warning('Dropping data from term %s for user %s',
                                   term, data['email'])
                    continue
                new_sch = {
                    'term': term,
                    'sections': [],
                    'updated': datetime.datetime.utcnow(),
                }
                new_sch['secret'] = (sch['sharing_key']
                                     or util.generate_secret())
                for section in sch['sections']:
                    try:
                        sect = {
                            'status': section['user_status'],
                            'id': find_section(term, section, c),
                            'updated': datetime.datetime.utcnow(),
                        }
                    except ValueError as e:
                        logging.error('At line %s:', i)
                        logging.error(e)
                        continue
                    if section['user_color']:
                        sect['color'] = section['user_color']
                    new_sch['sections'].append(sect)
                user['schedules'].append(new_sch)
            if data['is_admin']:
                user['roles'].append('admin')
            c.user.insert(user)
        except:
            LOGGER.error('Exception while processing line %s', i)
            raise

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    with app.test_request_context('/'):
        main(sys.argv[1:])
