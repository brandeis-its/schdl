from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import json
import unittest

from flask.ext import login

from schdl import mongo
from schdl import sessions
from schdl import test_data
from schdl import util
from schdl.wsgi import app


class TestHelpers(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_load_user(self):
        with test_data.Database.WithTestData() as data:
            c = mongo.SchoolCollections(data.school['fragment'])
            user = c.user.find_one()
            result = sessions.load_user('bad-id')
            self.assertIsNone(result)
            result = sessions.load_user('5269cb4dca50001cdb0a5daa')
            self.assertIsNone(result)
            result = sessions.load_user('%s:%s' % (data.school['fragment'],
                                                   user['_id']))
            data.user['_id'] = user['_id']
            self.assertEqual(result.user, data.user)

    def test_unauthorized(self):
        protected_paths = (
            ('/api/user', ('POST',)),
            ('/api/schedules/school/term/section', ('PUT', 'DELETE')),
            ('/api/student_interest/school/term', ('GET',)),
        )
        self.longMessage = True
        for path, methods in protected_paths:
            for method in methods:
                msg = 'Testing %s (%s)' % (path, method)
                result = self.app.open(path, method=method)
                self.assertEqual(result.status_code, 403, msg=msg)
                self.assertEqual(json.loads(result.data), dict(status='login'),
                                 msg=msg)


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

    def test_login_succeed(self):
        with test_data.Database.WithTestData() as data:
            response = self.login(data.school['fragment'], data.user['email'],
                                  data.user['clearpw'])
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
                json.loads(response.data))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(login.current_user['id'], data.user['id'])
        self.assertTrue(login.current_user.is_active())
        self.assertTrue(login.current_user.is_authenticated())
        self.assertFalse(login.current_user.is_anonymous())
        self.assertIsNotNone(login.current_user.get_id())

    def test_login_bad_pw(self):
        with test_data.Database.WithTestData() as data:
            response = self.login(data.school['fragment'], data.user['email'],
                                  'wrongpw')
        self.assertEqual(json.loads(response.data), {'reason': 'password'})
        self.assertEqual(response.status_code, 403)

    def test_login_bad_email(self):
        with test_data.Database.WithTestData() as data:
            response = self.login(data.school['fragment'], 'fake@email.com',
                                  'fakepw')
        self.assertEqual(json.loads(response.data), {'reason': 'noaccount'})
        self.assertEqual(response.status_code, 403)

    def test_logout(self):
        with test_data.Database.WithTestData() as data:
            self.login(data.school['fragment'], data.user['email'],
                       data.user['clearpw'])
            response = self.app.delete('/api/session')
        self.assertEqual(json.loads(response.data), dict(status='ok'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(login.current_user.is_active())
        self.assertFalse(login.current_user.is_authenticated())
        self.assertTrue(login.current_user.is_anonymous())
        self.assertIsNone(login.current_user.get_id())


if __name__ == '__main__':
    app.config.from_object('schdl.test_config')
    unittest.main()
