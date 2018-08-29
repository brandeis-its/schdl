from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import base64
import datetime
import re
import random
import string

from flask import json

from schdl import app
from schdl import mongo

NON_SEARCHABLE_CHARS = re.compile(r'(?:[^\w\s]|_)+', re.UNICODE)
WHITESPACE = re.compile(r'\s+', re.UNICODE)

JSON_ARGS = dict(allow_nan=False, separators=(',', ':'), sort_keys=True)

BRANDEIS_BOOKS_FORMAT = (
    'http://www.bkstr.com/webapp/wcs/stores/servlet/booklookServlet'
    '?bookstore_id-1=1391'
    '&term_id-1=%s'
    '&div-1='
    '&dept-1=%s'
    '&course-1=%s'
    '&sect-1=%s'
)


class Projection(object):
    def __init__(self, keys, _id=True):
        self._keys = set(keys)
        self._id = _id

    def __call__(self, obj):
        return {k: v for k, v in obj.iteritems() if k in self._keys}

    def mongo(self, _id=None):
        projection = {k: True for k in self._keys}
        if _id is None:
            _id = self._id
        if not _id:
            projection['_id'] = False
        return projection


def name(person):
    return ' '.join(person[part] for part in ('first', 'middle', 'last')
                    if person[part])


class User(object):
    def __init__(self, user, school):
        """Wrap a user dict.

        Args:
            user: dict containing user data
            school: dict containing school data
        """
        self.user = user
        self.school = school

    def name(self):
        return name(self.user) or 'Anonymous'

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return '%s:%s' % (self.school['fragment'], self.user['_id'])

    def __getitem__(self, key):
        return self.user[key]

    def __setitem__(self, key, value):
        self.user[key] = value

    def __delitem__(self, key):
        del self.user[key]

    def __contains__(self, key):
        return key in self.user

    def __iter__(self):
        return iter(self.user)

    def set_password(self, newpass):
        self.user['passhash'] = app.bcrypt.generate_password_hash(newpass)

    def __eq__(self, other):
        return other == self.user

    def formatSchedules(self, timestamps=False):
        schedules = []
        c = mongo.SchoolCollections(self.school['fragment'])
        for schedule in self.user['schedules']:
            term = c.term.find_one(
                {
                    'id': schedule['term']
                },
                project_term.mongo(),
            )
            schedules.append(self._formatSchedule(term, schedule, timestamps))
        return schedules

    def _formatSchedule(self, term, schedule, timestamps=False):
        out = {
            'term': term,
            # TODO(eitan): workaround for users with schedules with no secret -
            #              fix the data!
            'secret': schedule.get('secret', ''),
        }
        sections = []
        c = mongo.SchoolCollections(self.school['fragment'])
        for schdl_section in schedule['sections']:
            course = c.course.find_one(
                {
                    'sections.id': schdl_section['id']
                }, {
                    '_id': False,
                    'sections.$': True,
                    'name': True,
                    'code': True,
                    'fragment': True,
                    'independent_study': True,
                    'requirements': True,
                    'continuity_id': True,
                }
            )
            section = formatCourseSection(c, term, course, schdl_section['id'])
            section['user_status'] = schdl_section['status']
            if timestamps:
                # TODO(eitan): workaround for users with classes in their
                #              schedules that were added before 'updated' field
                #              existed
                section['user_updated'] = schdl_section.get(
                    'updated', datetime.datetime(2012, 1, 1))
            sections.append(section)
        out['course_sections'] = sections
        return out

    def hasPermissionTo(self, verb, resource):
        key = (verb, resource)
        roles = self.user.get('roles', [])
        if key == ('view', 'student_interest'):
            return 'registrar' in roles or 'admin' in roles
        else:
            return False


def getSchedule(user, term_id):
    for schedule in user['schedules']:
        if schedule['term'] == term_id:
            return schedule


def getScheduleCourseSection(schedule, section_id):
    for section in schedule['sections']:
        if section['id'] == section_id:
            return section


def findSectionInCourse(section_id, course):
    for section in course['sections']:
        if section['id'] == section_id:
            return section


project_course = Projection(
    (
        'name',
        'fragment',
        'requirements',
        'code',
        'description',
        'independent_study',
        'subjects',
    ),
    _id=False,
)

project_course_for_search = Projection(
    (
        'name',
        'code',
        'fragment',
        'requirements',
    ),
    _id=False,
)

project_instructor = Projection(
    (
        'first',
        'middle',
        'last',
        'email',
        'fragment',
        'id'
    ),
    _id=False,
)

project_section = Projection((
    'id',
    'section',
    'details',
    'instructors',
    'enrolled',
    'waiting',
    'limit',
    'status',
    'status_text',
    'times',
))

project_term = Projection(
    (
        'name',
        'fragment',
        'id',
        'start',
        'end',
    ),
    _id=False,
)


def formatCourseSection(c, term, course, section, instructors=True):
    if isinstance(section, basestring):
        section = findSectionInCourse(section, course)
    section = project_section(section)
    if c.school_fragment == 'brandeis':
        section['registration_id'] = section['id'].split('-')[1]
        section['books_url'] = brandeis_books_url(term, course, section)
    if instructors:
        section['instructors'] = get_instructors(c, section)
    else:
        del section['instructors']
    section['course_name'] = course['name']
    section['course_code'] = course['code']
    section['course_continuity_id'] = course['continuity_id']
    section['course_fragment'] = course['fragment']
    return encode_my_id(section)


def get_instructors(c, section):
    if not section['instructors']:
        return []
    instrs = c.instructor.find(
        {'id': {'$in': section['instructors']}},
        project_instructor.mongo(),
    )
    instrs = list(instrs)
    for instr in instrs:
        instr['name'] = name(instr)
    return instrs


def encode_section_id(section_id):
    return unicode(base64.urlsafe_b64encode(
        unicode(section_id).encode('utf-8')))


def decode_section_id(encoded_id):
    return unicode(base64.urlsafe_b64decode(str(encoded_id)), encoding='utf-8')


def encode_my_id(section):
    section['fragment'] = encode_section_id(section['id'])
    del section['id']
    return section


def make_searchable(string):
    return WHITESPACE.sub(' ', NON_SEARCHABLE_CHARS.sub('', string)).lower()


def generate_secret(chars=None, length=30):
    if chars is None:
        chars = string.ascii_uppercase + string.digits
    rand = random.SystemRandom()
    return ''.join(rand.choice(chars) for i in xrange(length))


def create_verification(c, type_, ttl=None, **payload):
    if ttl is None:
        ttl = datetime.timedelta(days=30)
    verification = payload
    verification['type'] = type_
    verification['expiration'] = datetime.datetime.utcnow() + ttl
    # TODO(eitan): retry on duplicate key error
    verification['secret'] = generate_secret()
    c.email_verification.insert(verification, w=1)
    return verification['secret']


def brandeis_books_url(term, course, section):
    if term['id'] > '1142':
      return BRANDEIS_BOOKS_FORMAT % (
          (term['id'],) +
          tuple(course['code'].split(None, 1)) +
          (section['section'],)
      )


class RouteSet(object):
    """Ordered collection of routing rules.

    Create one instance per module, then use the add method as a decorator like
    app.route or the append method, which accepts the same arguments as
    app.add_url_rule.
    """

    def __init__(self):
        self.routes = []

    def add(self, *args, **kwargs):
        def decorator(view_func):
            _kwargs = kwargs.copy()
            _kwargs['view_func'] = view_func
            self.routes.append((args, _kwargs))
            return view_func
        return decorator

    def append(self, *args, **kwargs):
        self.routes.append((args, kwargs))

    def apply(self, app):
        for args, kwargs in self.routes:
            app.add_url_rule(*args, **kwargs)
