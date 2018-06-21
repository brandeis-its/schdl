from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import unittest

from schdl import app
from schdl import test_data
from schdl.model import *


class TestUser(unittest.TestCase):
    def setUp(self):
        self.user = User()

    def test_dummy_functions(self):
        """Test dummy functions included for the sake of peewee-login."""
        self.assertIs(self.user.is_active(), True)
        self.assertIs(self.user.is_authenticated(), True)
        self.assertIs(self.user.is_anonymous(), False)

#    TODO(eitan): deleted this function because creating a user in test_data
#    seems to fail by calling get_id when calling save()
#    def test_get_id(self):
#        with self.assertRaises(AssertionError):
#            self.user.get_id()
#        self.user.id = 598
#        self.assertEqual(self.user.get_id(), u'598')

    def test_name(self):
        self.assertEqual(self.user.name(), u'Anonymous')
        self.user.first = u'John'
        self.assertEqual(self.user.name(), u'John')
        self.user.last = u'Public'
        self.assertEqual(self.user.name(), u'John Public')
        self.user.middle = u'Q.'
        self.assertEqual(self.user.name(), u'John Q. Public')
        self.user.last = None
        self.assertEqual(self.user.name(), u'John Q.')
        self.user.first = u''
        self.assertEqual(self.user.name(), u'Q.')
        self.user.middle = None
        self.user.last = u'Public'
        self.assertEqual(self.user.name(), u'Public')

    def test_password(self):
        self.assertIsNone(self.user.passhash)
        with self.assertRaises(AttributeError):
            self.user.password
        self.user.password = u'foo'
        self.assertTrue(self.user.passhash)
        self.assertTrue(
            app.bcrypt.check_password_hash(self.user.passhash, 'foo'))

    def test_GetSchedule_Exists(self):
        with test_data.Database.WithTestData(user=True,
                                             term=True,
                                             schedule=True) as data:
            result = data.user.GetSchedule(data.term)
            self.assertEqual(result, data.schedule)
            result = data.user.GetSchedule(data.term, create=True)
            self.assertEqual(result, data.schedule)

    def test_GetSchedule_DoesNotExist(self):
        with test_data.Database.WithTestData(user=True,
                                             term=True,
                                             schedule=True) as data:
            result = data.user.GetSchedule(999)
            self.assertIsNone(result)
            result = data.user.GetSchedule(999, create=True)
            self.assertEqual(result._data['term'], 999)


class TestSchool(unittest.TestCase):
    def setUp(self):
        self.school = test_data.School.make()

    def test_POD(self):
        self.assertEqual(self.school.POD(), {
            'name': self.school.name, 'id': self.school.url,
            'website': self.school.website
        })

    def test_POD_with_testDB(self):
        with test_data.Database.WithTestData(school=True):
            school = School.get(School.url == self.school.url)
            self.assertEqual(school.POD(), {
                'name': self.school.name, 'id': self.school.url,
                'website': self.school.website
            })


class TestTerm(unittest.TestCase):
    def setUp(self):
        self.term = test_data.Term.make()

    def test_POD(self):
        self.assertEqual(self.term.POD(), {
            'name': 'Spring 2013', 'id': 'Spring_2013', 'start': '2013-01-21',
            'end': '2013-04-21'
        })


class TestSubject(unittest.TestCase):
    def setUp(self):
        self.subject = test_data.Subject.make()

    def test_POD(self):
        self.assertEqual(self.subject.POD(), {
            'name': self.subject.name, 'id': self.subject.url
        })

    def test_get_cross_listings(self):
        with test_data.Database.WithTestData(school=True,
                                             subject=True,
                                             course=True) as data:
            self.assertEqual(list(data.subject.get_cross_listings()),
                             [data.course])


class TestCourse(unittest.TestCase):
    def setUp(self):
        self.course = test_data.Course.make()

    def test_POD(self):
        self.assertEqual(self.course.POD(), {
            'name': self.course.name,
            'code': self.course.code,
            'id': self.course.url,
            'description': self.course.description
        })


class TestCourseSection(unittest.TestCase):
    def setUp(self):
        self.cs = test_data.CourseSection.make()

    def test_POD(self):
        self.cs.course = test_data.Course.make()
        self.cs.times = [CourseTime(school=1, course_section=self.cs,
                                    start=600, end=650, m=True, w=True)]
        self.assertEqual(self.cs.POD(), {
            'course': self.cs.course.url,
            'course_name': self.cs.course.name,
            'course_code': self.cs.course.code,
            'section': self.cs.section,
            'details': self.cs.details,
            'status': self.cs.status,
            'enrolled': self.cs.enrolled,
            'waiting': self.cs.waiting,
            'limit': self.cs.limit,
            'id': self.cs.id,
            'times': [time.POD() for time in self.cs.times]
        })


class TestCourseTime(unittest.TestCase):
    def setUp(self):
        self.ct = CourseTime(school=1, course_section=1, start=600, end=650,
                             m=True, w=True, f=True, type='Lab',
                             building='Shapiro', room='123')

    def test_POD(self):
        self.assertEqual(self.ct.POD(), {
            'start': self.ct.start,
            'end': self.ct.end,
            'su': self.ct.su,
            'm': self.ct.m,
            'tu': self.ct.tu,
            'w': self.ct.w,
            'th': self.ct.th,
            'f': self.ct.f,
            'sa': self.ct.sa,
            'type': self.ct.type,
            'building': self.ct.building,
            'room': self.ct.room
        })


class TestRequirement(unittest.TestCase):
    def setUp(self):
        self.req = test_data.Requirement.make()

    def test_POD(self):
        self.assertEqual(self.req.POD(), {
            'short_name': self.req.short,
            'long_name': self.req.long
        })


class TestInstructor(unittest.TestCase):
    def setUp(self):
        self.instr = test_data.Instructor.make()

    def test_POD(self):
        self.assertEqual(self.instr.POD(), {
            'id': self.instr.url,
            'first': self.instr.first,
            'middle': self.instr.middle,
            'last': self.instr.last,
            'name': self.instr.name()
        })

    def test_get_course_sections(self):
        with test_data.Database.WithTestData(instructor=True,
                                             term=True,
                                             course=True,
                                             school=True,
                                             course_section=True) as data:
            result = data.instructor.get_course_sections()
            self.assertEqual(list(result), [data.course_section])


class TestSchedule(unittest.TestCase):
    def setUp(self):
        self.schedule = test_data.Schedule.make()

    def test_POD(self):
        with test_data.Database.WithTestData(school=True,
                                             term=True,
                                             course=True,
                                             course_section=True,
                                             schedule=True) as data:
            cs_pod = data.course_section.POD()
            cs_pod['color'] = 'red'
            cs_pod['user_status'] = 'considering'
            self.assertEqual(data.schedule.POD(), {
                'school': data.school.POD(),
                'term': data.term.POD(),
                'course_sections': [cs_pod]
            })

if __name__ == '__main__':
    app.config.from_object('schdl.test_config')
    unittest.main()
