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

    def test_student_interest_json(self):
        with test_data.Database.WithTestData() as data:
            response = self.app.get(
                    '/api/student_interest/%s/%s'
                    % (data.school['fragment'], data.term['fragment']))
            self.assertEqual(json.loads(response.data), dict(status='login'))
            self.assertEqual(response.status_code, 403)
            self.login(data.school['fragment'], data.user['email'],
                       data.user['clearpw'])
            response = self.app.get(
                    '/api/student_interest/%s/%s'
                    % (data.school['fragment'], data.term['fragment']))
            self.assertEqual(json.loads(response.data), dict(reason='permission_denied'))
            self.assertEqual(response.status_code, 403)
        with test_data.Database.WithTestData(user_roles=['admin']) as data:
            self.login(data.school['fragment'], data.user['email'],
                       data.user['clearpw'])
            response = self.app.get(
                    '/api/student_interest/%s/%s'
                    % (data.school['fragment'], data.term['fragment']))
            self.assertEqual(json.loads(response.data), [{'course_name': 'Introductory Basket Weaving', 'course_fragment': 'BW101', 'no': 0, 'maybe': 0, 'section': '1', 'official': 1, 'definitely': 0, 'course_code': 'BW101', 'total': 1, 'id': 'bw-1'}])
            self.assertEqual(response.status_code, 200)
        with test_data.Database.WithTestData(user_roles=['registrar']) as data:
            self.login(data.school['fragment'], data.user['email'],
                       data.user['clearpw'])
            response = self.app.get(
                    '/api/student_interest/%s/%s'
                    % (data.school['fragment'], data.term['fragment']))
            self.assertEqual(json.loads(response.data), [{'course_name': 'Introductory Basket Weaving', 'course_fragment': 'BW101', 'no': 0, 'maybe': 0, 'section': '1', 'official': 1, 'definitely': 0, 'course_code': 'BW101', 'total': 1, 'id': 'bw-1'}])
            self.assertEqual(response.status_code, 200)

    def test_student_interest_csv(self):
        with test_data.Database.WithTestData() as data:
            response = self.app.get(
                    '/api/student_interest/%s/%s.csv'
                    % (data.school['fragment'], data.term['fragment']))
            self.assertEqual(json.loads(response.data), dict(status='login'))
            self.assertEqual(response.status_code, 403)
            self.login(data.school['fragment'], data.user['email'],
                       data.user['clearpw'])
            response = self.app.get(
                    '/api/student_interest/%s/%s.csv'
                    % (data.school['fragment'], data.term['fragment']))
            self.assertEqual(json.loads(response.data), dict(reason='permission_denied'))
            self.assertEqual(response.status_code, 403)
        with test_data.Database.WithTestData(user_roles=['admin']) as data:
            self.login(data.school['fragment'], data.user['email'],
                       data.user['clearpw'])
            response = self.app.get(
                    '/api/student_interest/%s/%s.csv'
                    % (data.school['fragment'], data.term['fragment']))
            self.assertEqual(response.data,
                    'Course Code,Section,Course Name,Interested,Decided to Take,Officially Enrolled,Total Interest,Ruled Out\r\n'
                    'BW101,1,Introductory Basket Weaving,0,0,1,1,0\r\n')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.mimetype, 'text/csv')
        with test_data.Database.WithTestData(user_roles=['registrar']) as data:
            self.login(data.school['fragment'], data.user['email'],
                       data.user['clearpw'])
            response = self.app.get(
                    '/api/student_interest/%s/%s.csv'
                    % (data.school['fragment'], data.term['fragment']))
            self.assertEqual(response.data,
                    'Course Code,Section,Course Name,Interested,Decided to Take,Officially Enrolled,Total Interest,Ruled Out\r\n'
                    'BW101,1,Introductory Basket Weaving,0,0,1,1,0\r\n')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.mimetype, 'text/csv')

if __name__ == '__main__':
    app.config.from_object('schdl.test_config')
    unittest.main()
