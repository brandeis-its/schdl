from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import json
import unittest

from schdl import mongo
from schdl import test_data
from schdl import util
from schdl.wsgi import app


class TestUpdateSchedule(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.maxDiff = None

    def login(self, school, email, pw):
        request_body = json.dumps(dict(email=email, password=pw))
        response = self.app.post('/api/session/%s' % school,
                                 data=request_body,
                                 content_type='application/json')
        return response

    def test_DELETE(self):
        with test_data.Database.WithTestData() as data:
            c = mongo.SchoolCollections(data.school['fragment'])
            user = util.User(
                c.user.find_one({'id': data.user['id']}),
                data.school)
            self.assertTrue(user['schedules'][0]['sections'])
            self.login(data.school['fragment'], data.user['email'],
                       data.user['clearpw'])
            # Delete a fake section
            response = self.app.delete('/api/schedules/%s/%s/%s'
                                       % (data.school['fragment'],
                                          data.term['fragment'],
                                          util.encode_section_id(
                                              'fake-section')))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                {
                    'name': user.name(),
                    'first': user['first'],
                    'middle': user['middle'],
                    'last': user['last'],
                    'email': user['email'],
                    'roles': {},
                    'secret': user['secret'],
                    'schedules': [
                        user._formatSchedule(
                            util.project_term(data.term), data.user['schedules'][0])
                    ],
                },
                json.loads(response.data)
            )
            # Delete a real section
            response = self.app.delete('/api/schedules/%s/%s/%s'
                                       % (data.school['fragment'],
                                          data.term['fragment'],
                                          util.encode_section_id(
                                              data.course_section['id'])))
            self.assertEqual(response.status_code, 200)
            user['schedules'][0]['sections'] = []
            self.assertEqual(
                {
                    'name': user.name(),
                    'first': user['first'],
                    'middle': user['middle'],
                    'last': user['last'],
                    'email': user['email'],
                    'roles': {},
                    'secret': user['secret'],
                    'schedules': [
                        user._formatSchedule(
                            util.project_term(data.term), user['schedules'][0])
                    ],
                },
                json.loads(response.data)
            )
            user = util.User(
                c.user.find_one({'id': data.user['id']}),
                data.school)
            self.assertFalse(user['schedules'][0]['sections'])

    def test_PUT(self):
        with test_data.Database.WithTestData() as data:
            c = mongo.SchoolCollections(data.school['fragment'])
            user = c.user.find_one({'id': data.user['id']})
            self.assertEqual(data.schedule['sections'][0]['status'],
                             user['schedules'][0]['sections'][0]['status'])
            self.login(data.school['fragment'], data.user['email'],
                       data.user['clearpw'])
            response = self.app.put('/api/schedules/%s/%s/%s'
                                    % (data.school['fragment'],
                                       data.term['fragment'],
                                       util.encode_section_id(
                                           data.course_section['id'])),
                                    data=json.dumps(dict(status='no')),
                                    content_type='application/json')
            self.assertEqual(response.status_code, 200)
            user = util.User(
                c.user.find_one({'id': data.user['id']}),
                data.school)
            self.assertEqual('no',
                             user['schedules'][0]['sections'][0]['status'])
            self.assertEqual(
                {
                    'name': user.name(),
                    'first': user['first'],
                    'middle': user['middle'],
                    'last': user['last'],
                    'email': user['email'],
                    'roles': {},
                    'secret': user['secret'],
                    'schedules': [
                        user._formatSchedule(
                            util.project_term(data.term), user['schedules'][0])
                    ],
                },
                json.loads(response.data)
            )

if __name__ == '__main__':
    app.config.from_object('schdl.test_config')
    unittest.main()
