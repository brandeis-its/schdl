from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import json
import unittest

from schdl import mongo
from schdl import test_data
from schdl import util
from schdl.wsgi import app


# TODO(eitan): assert that no API object contains an 'id' field
class TestBrowse(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.maxDiff = None

    def test_schools(self):
        with test_data.Database.WithTestData() as data:
            response = self.app.get('/api/schools')
        school = data.school
        del school['hostname']
        self.assertEqual(json.loads(response.data), [school])

    def test_school(self):
        with test_data.Database.WithTestData() as data:
            response = self.app.get('/api/schools/' + data.school['fragment'])
        expect = data.school
        term = util.project_term(data.term)
        del term['id'], expect['hostname']
        expect['terms'] = [term]
        expect['requirements'] = [data.requirement]
        self.assertEqual(json.loads(response.data), expect)

    def test_term(self):
        with test_data.Database.WithTestData() as data:
            response = self.app.get('/api/terms/%s/%s'
                                    % (data.school['fragment'],
                                       data.term['fragment']))
        expect = data.term
        del expect['id']
        expect['subjects'] = [data.subject]
        self.assertEqual(expect, json.loads(response.data))

    def test_subject(self):
        with test_data.Database.WithTestData() as data:
            response = self.app.get('/api/subjects/%s/%s/%s'
                                    % (data.school['fragment'],
                                       data.term['fragment'],
                                       data.subject['fragment']))
        expect = data.subject
        expect['term'] = util.project_term(data.term)
        del expect['term']['id']
        # TODO(eitan): add more courses to test_data and assert they are
        # natsorted by key
        # TODO(eitan): add more than one segment
        course = util.project_course(data.course)
        del course['subjects']
        expect['segments'] = [{'courses': [course]}]
        del data.course['sections']
        self.assertEqual(expect, json.loads(response.data))

    def test_course(self):
        with test_data.Database.WithTestData() as data:
            response = self.app.get('/api/courses/%s/%s/%s'
                                    % (data.school['fragment'],
                                       data.term['fragment'],
                                       data.course['fragment']))
        self.assertEqual(response.status_code, 200)
        section = util.encode_my_id(data.course_section)
        instructor = util.project_instructor(data.instructor)
        instructor['name'] = util.name(instructor)
        section['instructors'] = [instructor]
        expect = data.course
        expect['term'] = data.term
        del expect['term']['subjects']
        expect['subjects'] = [data.subject]
        del data.subject['segments']
        expect['sections'] = [section]
        expect['other_terms'] = []
        expect['requirements'] = [data.requirement['id']]
        self.assertEqual(expect, json.loads(response.data))

    def test_instructor(self):
        with test_data.Database.WithTestData() as data:
            response = self.app.get('/api/instructors/%s/%s'
                                    % (data.school['fragment'],
                                       data.instructor['fragment']))
            c = mongo.SchoolCollections(data.school['fragment'])
        self.assertEqual(response.status_code, 200)
        # TODO(eitan): this test would be more meaningful with multiple terms &
        # multiple sections/term
        expect = util.project_instructor(data.instructor)
        expect['name'] = util.name(expect)
        term = util.project_term(data.term)
        cs = util.formatCourseSection(c, term, data.course, data.course_section,
                                      instructors=False)
        term['course_sections'] = [cs]
        # TODO(eitan): better to have an IS
        term['independent_studies'] = []
        expect['terms'] = [term]
        self.assertEqual(expect, json.loads(response.data))

if __name__ == '__main__':
    app.config.from_object('schdl.test_config')
    unittest.main()
