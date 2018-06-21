from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import itertools
import functools
import logging
import operator
import re

import flask
from flask import json
from flask import request
import natsort

from schdl import app
from schdl import mongo
from schdl import util


LOGGER = logging.getLogger(__name__)

routes = util.RouteSet()


@routes.add('/api/schools')
def schools():
    schools = list(app.mongo.db.schools.find(
        None,
        {'_id': False, 'hostname': False, 'api_key_hash': False},
    ))
    return flask.Response(json.dumps(schools), mimetype='application/json')


def _termsForSchool(school):
    terms = mongo.SchoolCollections(school).term.find(
        {'hasCourses': True},
        {'subjects': False, '_id': False, 'id': False, 'hasCourses': False},
    )
    return sorted(terms, key=lambda t: t['start'], reverse=True)


def _requirementsForSchool(school):
    requirements = list(mongo.SchoolCollections(school).requirement.find(
        None,
        {'_id': False},
    ))
    requirements.sort(key=lambda x: x['short'])
    return list(requirements)


@routes.add('/api/schools/host:<hostname>')
def schoolByHostName(hostname):
    school = app.mongo.db.schools.find_one_or_404(
        {'hostname': hostname},
        {'_id': False, 'hostname': False, 'api_key_hash': False},
    )
    school['terms'] = _termsForSchool(school['fragment'])
    school['requirements'] = _requirementsForSchool(school['fragment'])
    return json.jsonify(school)


@routes.add('/api/schools/<school>')
def school(school):
    school = app.mongo.db.schools.find_one_or_404(
        {'fragment': school},
        {'_id': False, 'hostname': False, 'api_key_hash': False},
    )
    school['terms'] = _termsForSchool(school['fragment'])
    school['requirements'] = _requirementsForSchool(school['fragment'])
    return json.jsonify(school)


@routes.add('/api/terms/<school>/<term>')
def term(school, term):
    app.mongo.db.schools.find_one_or_404({'fragment': school},
                                         {'_id': True})
    out = mongo.SchoolCollections(school).term.find_one_or_404(
        {'fragment': term}, {'_id': False, 'id': False})
    out['subjects'] = [subj for subj in out['subjects'] if subj['hasCourses']]
    out['subjects'].sort(key=lambda x: x['name'])
    return json.jsonify(out)


@routes.add('/api/subjects/<school>/<term>/<subject>')
def subject(school, term, subject):
    app.mongo.db.schools.find_one_or_404({'fragment': school},
                                         {'_id': True})
    c = mongo.SchoolCollections(school)
    term = c.term.find_one_or_404(
        {'fragment': term, 'subjects.fragment': subject},
        {
            'fragment': True,
            'name': True,
            'start': True,
            'end': True,
            'subjects.$': True,
            '_id': False,
        })
    out = term['subjects'][0]
    del term['subjects']
    out['term'] = term
    courses = {segment['id']: [] for segment in out['segments']}
    courses[None] = []
    for course in c.course.find(
            {'subjects.id': out['id']}, util.project_course.mongo()):
        for subject in course['subjects']:
            if subject['id'] != out['id']:
                continue
            segment = subject.get('segment', None)
            courses[segment].append(course)
        del course['subjects']

    for segment in courses.itervalues():
        segment.sort(key=lambda(course):
                     natsort.natsort_key(course['code'], number_type=None))

    segments = []
    if courses[None]:
        segments.append({'courses': courses[None]})
    for segment in out['segments']:
        if courses[segment['id']]:
            segments.append({
                'name': segment['name'],
                'courses': courses[segment['id']]
            })
    out['segments'] = segments

    return json.jsonify(out)


@routes.add('/api/courses/<school>/<term>/<course>')
def course(school, term, course):
    app.mongo.db.schools.find_one_or_404({'fragment': school},
                                         {'_id': True})
    c = mongo.SchoolCollections(school)
    term = c.term.find_one_or_404({'fragment': term},
                                  {'_id': False})
    subjects = term['subjects']
    del term['subjects']
    course = c.course.find_one_or_404(
        {'term': term['id'], 'fragment': course}, {'_id': False})
    for section in course['sections']:
        if c.school_fragment == 'brandeis':
            section['registration_id'] = section['id'].split('-')[1]
            section['books_url'] = util.brandeis_books_url(
                term, course, section)
        section['instructors'] = util.get_instructors(c, section)
        util.encode_my_id(section)
    out = course
    course_subjects = set(subj['id'] for subj in out['subjects'])
    subjects = [subj for subj in subjects if subj['id'] in course_subjects]
    # This currently fails for a bunch of courses with code RBIF xyz because
    # they point to non-existent subjects.
    # assert len(subjects) == len(course_subjects)
    for subj in subjects:
        del subj['segments']
    other_terms = []
    for alt_course in c.course.find(
        {
            'continuity_id': course['continuity_id'],
            'id': {'$ne': course['id']}
        },
        {'term': True, 'name': True, 'fragment': True, '_id': False}
    ):
        alt_term = c.term.find_one(
            {'id': alt_course['term']},
            {'_id': False, 'fragment': True, 'name': True, 'end': True})
        assert alt_term
        alt_course['term'] = alt_term
        other_terms.append(alt_course)
    out['term'] = term
    out['subjects'] = subjects
    out['other_terms'] = other_terms
    return json.jsonify(out)


@routes.add('/api/instructors/<school>/<instructor>')
def instructor(school, instructor):
    app.mongo.db.schools.find_one_or_404({'fragment': school},
                                         {'_id': True})
    c = mongo.SchoolCollections(school)
    get_term = lambda course: course['term']
    instructor = c.instructor.find_one_or_404(
        {'fragment': instructor}, util.project_instructor.mongo())
    instructor['name'] = util.name(instructor)
    courses = c.course.find(
        {'sections.instructors': instructor['id']},
        {'_id': False})
    terms = []
    courses = sorted(courses, key=get_term)
    for term_id, course_iter in itertools.groupby(courses, get_term):
        term = c.term.find_one(
            {'id': term_id}, util.project_term.mongo())
        assert term
        term['course_sections'] = []
        term['independent_studies'] = []
        for course in course_iter:
            for section in course['sections']:
                if instructor['id'] not in section['instructors']:
                    continue
                section = util.formatCourseSection(c, term, course, section,
                                                   instructors=False)
                if course['independent_study']:
                    term['independent_studies'].append(section)
                else:
                    term['course_sections'].append(section)
        for to_sort in (term['course_sections'], term['independent_studies']):
            to_sort.sort(key=lambda(section):
                         natsort.natsort_key(section['course_code'],
                                             number_type=None))
        terms.append(term)
    terms.sort(key=operator.itemgetter('start', 'end'), reverse=True)
    out = instructor
    out['terms'] = terms
    return json.jsonify(out)


@routes.add('/api/quicksearch/<school>/<term>')
def quicksearch(school, term):
    app.mongo.db.schools.find_one_or_404({'fragment': school},
                                         {'_id': True})
    c = mongo.SchoolCollections(school)
    term_obj = c.term.find_one_or_404(
        {'fragment': term}, {'_id': False, 'id': True})
    query = util.make_searchable(re.escape(request.args['query']))
    courses = c.course.find({
        'term': term_obj['id'],
        '$or': [
            {'searchable_code': {'$regex': query}},
            {'searchable_name': {'$regex': query}},
        ],
    }, {
        '_id': False,
        'name': True,
        'code': True,
        'fragment': True
    }, limit=app.config.get('SCHDL_QUICKSEARCH_LIMIT', 100))
    courses = list(courses)
    courses.sort(key=functools.partial(_quicksearch_sort_key, query))
    return flask.Response(json.dumps(courses), mimetype='application/json')


def _quicksearch_sort_key(query, course):
    name_index = util.make_searchable(course['name']).find(query)
    code_index = util.make_searchable(course['code']).find(query)
    if name_index == -1:
        name_index = 9999
    if code_index == -1:
        code_index = 9999
    return min(name_index, code_index), name_index + code_index


@routes.add('/api/subject_search/<school>/<term>')
def qs_subj(school, term):
    app.mongo.db.schools.find_one_or_404({'fragment': school},
                                         {'_id': True})
    c = mongo.SchoolCollections(school)
    term = c.term.find_one_or_404(
        {'fragment': term},
        {
            'subjects.name': True,
            'subjects.searchable_name': True,
            'subjects.searchable_abbreviation': True,
            'subjects.id': True,
            '_id': False
        }
    )
    query = util.make_searchable(re.escape(request.args['query']))
    subjects = [subj for subj in term['subjects']
                if query in subj['searchable_name']
                or query in subj['searchable_abbreviation']]
    for subj in subjects:
        del subj['searchable_name'], subj['searchable_abbreviation']
    return flask.Response(json.dumps(subjects), mimetype='application/json')


@routes.add('/api/subject_lookup/<school>/<term>')
def subject_lookup(school, term):
    app.mongo.db.schools.find_one_or_404({'fragment': school},
                                         {'_id': True})
    c = mongo.SchoolCollections(school)
    term = c.term.find_one_or_404(
        {'fragment': term},
        {
            'subjects.name': True,
            'subjects.id': True,
            '_id': False
        }
    )
    query = request.args.getlist('subj')
    subjects = [subj for subj in term['subjects'] if subj['id'] in query]
    return flask.Response(json.dumps(subjects), mimetype='application/json')


@routes.add('/api/instructor_search/<school>')
def qs_instructor(school):
    app.mongo.db.schools.find_one_or_404({'fragment': school},
                                         {'_id': True})
    c = mongo.SchoolCollections(school)
    query = util.make_searchable(re.escape(request.args['query']))
    instructors = list(c.instructor.find(
        {'searchable_name': {'$regex': query}},
        {
            'name': True,
            'id': True,
            'fragment': True,
            '_id': False
        }
    ))
    # TODO(eitan): sort
    return flask.Response(json.dumps(instructors), mimetype='application/json')


@routes.add('/api/instructor_lookup/<school>')
def instructor_lookup(school):
    app.mongo.db.schools.find_one_or_404({'fragment': school},
                                         {'_id': True})
    c = mongo.SchoolCollections(school)
    query = request.args.getlist('instr')
    instructors = list(c.instructor.find(
        {'id': {'$in': query}},
        {
            'name': True,
            'id': True,
            'fragment': True,
            '_id': False
        }
    ))
    # TODO(eitan): sort
    return flask.Response(json.dumps(instructors), mimetype='application/json')


@routes.add('/api/search/<school>')
def search(school):
    school = app.mongo.db.schools.find_one_or_404(
        {'fragment': school},
        {
            'requirements': True,
            'fragment': True,
        },
    )
    # Exclude courses without sections
    query = {'sections.0': {'$exists': 1}}
    params = request.args
    if params.get('independent_study', 'false') != 'true':
        query['independent_study'] = False
    if params.get('closed', 'false') != 'true':
        query['sections.status'] = {'$in': ['open', 'restricted']}
    c = mongo.SchoolCollections(school['fragment'])
    if 'term' in params:
        term = c.term.find_one_or_404({'fragment': params['term']},
                                      {'id': True, '_id': False})
        query['term'] = term['id']
    if 'req' in params:
        operator = '$in' if 'reqAny' in params else '$all'
        query['requirements'] = {operator: params.getlist('req')}
    if 'subj' in params:
        query['subjects.id'] = {'$in': params.getlist('subj')}
    if 'instr' in params:
        query['sections.instructors'] = {'$in': params.getlist('instr')}
    if 'q' in params:
        q = util.make_searchable(re.escape(request.args['q']))
        query['$or'] = [
            {'searchable_code': {'$regex': q}},
            {'searchable_name': {'$regex': q}},
            {'searchable_description': {'$regex': q}},
            {'sections.searchable_details': {'$regex': q}},
        ]
    results = list(c.course.find(
        query,
        util.project_course_for_search.mongo()
    ))
    return flask.Response(json.dumps(results), mimetype='application/json')


@routes.add('/api/testExceptionHandler')
def testExceptionHandler():
    assert False, 'This is just a test.'
