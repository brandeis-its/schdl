from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import json
import unittest

from schdl import test_data
from schdl import util
from schdl.wsgi import app


class TestRoutes(unittest.TestCase):
    def setUp(self):
        self._app = app.test_client()
        self.app = self._app.__enter__()
        self.maxDiff = None

    def tearDown(self):
        self._app.__exit__(None, None, None)
        self.app = None

    def login(self, school, email, pw):
        request_body = json.dumps(dict(email=email, password=pw))
        response = self.app.post('/api/session/%s' % school,
                                 data=request_body,
                                 content_type='application/json')
        return response

    def test_user_info(self):
        with test_data.Database.WithTestData() as data:
            response = self.app.get('/api/user')
            self.assertIsNone(json.loads(response.data))
            self.assertEqual(response.status_code, 200)
            self.login(data.school['fragment'], data.user['email'],
                       data.user['clearpw'])
            response = self.app.get('/api/user')
            self.assertEqual(response.status_code, 200)
            user = util.User(data.user, data.school)
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

if __name__ == '__main__':
    app.config.from_object('schdl.test_config')
    unittest.main()
