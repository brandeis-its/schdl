from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import contextlib

import mongomock
from flask.ext import pymongo

from schdl import app
from schdl import mongo


class Database(object):
    def __init__(self):
        self.school = School.make()
        c = mongo.SchoolCollections(self.school['fragment'])
        self.term = Term.make()
        self.subject = Subject.make()
        self.term['subjects'] = [self.subject]
        self.requirement = Requirement.make(term=self.term)
        self.course = Course.make(term=self.term, subject=self.subject,
                                  requirement=self.requirement)
        self.instructor = Instructor.make()
        self.course_section = CourseSection.make(term=self.term,
                                                 course=self.course,
                                                 instructor=self.instructor)
        self.course['sections'] = [self.course_section]
        self.user = User.make()
        self.schedule = Schedule.make(self.school, self.term,
                                      self.course_section)
        self.user['schedules'] = [self.schedule]
        app.mongo.db.schools.insert(self.school.copy())
        c.term.insert(self.term.copy())
        c.course.insert(self.course.copy())
        c.requirement.insert(self.requirement.copy())
        c.instructor.insert(self.instructor.copy())
        c.user.insert(self.user.copy())

    @classmethod
    @contextlib.contextmanager
    def WithTestData(cls):
        assert app.config['MONGO_TEST_METHOD'] in ('mongomock', 'live')
        prev_value = app.mongo
        if app.config['MONGO_TEST_METHOD'] == 'mongomock':
            app.mongo = mongomock.Connection()
        else:  # app.config['MONGO_TEST_METHOD'] == 'live'
            app.mongo = TestMongo()
            app.mongo.db.connection.drop_database(app.mongo.db)
        try:
            yield cls()
        finally:
            app.mongo = prev_value


class TestMongo(object):
    def __init__(self):
        client = pymongo.MongoClient()
        self.db = client['test_' + app.name]


class User(object):
    @staticmethod
    def make():
        user = {
            'id': 103,
            'first': 'John',
            'middle': 'Q.',
            'last': 'Public',
            'email': ['john.q@public.gov'],
            'passhash': '$2a$04$R6FzjLsd.KNgL36MUKlArOhCLNN80DGq0C7'
                        'N16e2nvboEk.8bQtru',
            'created': '2013-04-01',
            'clearpw': 'jqpublic',
            'roles': [],
            'secret': 'notagoodsecret',
        }
        return user


class School(object):
    @staticmethod
    def make():
        school = {
            'name': 'Test University',
            'fragment': 'testu',
            'email_domain': 'test.edu',
            'website': 'http://www.test.edu',
            'hostname': ['schdl.test.edu'],
        }
        return school


class Term(object):
    @staticmethod
    def make():
        term = {
            'id': '1301',
            'name': 'Spring 2013',
            'fragment': 'Spring_2013',
            'start': '2013-01-21',
            'end': '2013-04-21',
            'hasCourses': True,
        }
        return term


class Subject(object):
    @staticmethod
    def make():
        subject = {
            'id': 'bw',
            'name': 'Basket Weaving',
            'abbreviation': 'BW',
            'fragment': 'BW',
            'course_count': 1,
            'segments': [],
            'hasCourses': True,
            'updated': '2013-04-21',
        }
        return subject


class Course(object):
    @staticmethod
    def make(term=None, subject=None, requirement=None):
        course = {
            'id': 'bw101',
            'term': term['id'],
            'subjects': [{'id': subject['id']}],
            'code': 'BW101',
            'fragment': 'BW101',
            'name': 'Introductory Basket Weaving',
            'description': 'foo',
            'continuity_id': 'bw_101',
            'requirements': [requirement['id']],
            'independent_study': False,
            'updated': '2013-04-21',
        }
        return course


class CourseSection(object):
    @staticmethod
    def make(term=None, course=None, instructor=None):
        cs = {
            'id': 'bw-1',
            'course': course['id'],
            'section': '1',
            'details': 'This section is fake.',
            'instructors': [instructor['id']],
            'status': 'Open',
            'enrolled': 5,
            'limit': 10,
            'waiting': 0,
            'minutes': 0,
            'updated': '2013-04-21',
            'times': [{'start': 600, 'end': 650, 'days': ['m', 'w']}],
        }
        return cs


class Requirement(object):
    @staticmethod
    def make(term=None):
        req = {
            'id': 'pe',
            'term': term['id'],
            'short': 'pe',
            'long': 'Physical Education',
            'updated': '2013-04-21',
        }
        return req


class Instructor(object):
    @staticmethod
    def make():
        instr = {
            'id': 'tjhickey',
            'email': 'tjhickey@testu.edu',
            'first': 'Tim',
            'middle': 'J.',
            'last': 'Hickey',
            'fragment': 'tjhickey',
            'updated': '2013-04-21',
        }
        return instr


class Schedule(object):
    @staticmethod
    def make(school=None, term=None, course_section=None):
        schedule = {
            'term': term['id'],
            'sections': [{
                'status': 'official',
                'id': course_section['id'],
            }],
        }
        return schedule
