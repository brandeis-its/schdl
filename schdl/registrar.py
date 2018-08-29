from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import csv
import flask
import io
import json
import logging

import flask_login

from schdl import app
from schdl import mongo
from schdl import schedules
from schdl import util

LOGGER = logging.getLogger(__name__)

routes = util.RouteSet()


@flask_login.login_required
def student_interest_data(school, term):
    if not flask_login.current_user.hasPermissionTo('view', 'student_interest'):
        return flask.jsonify(reason='permission_denied'), 403
    app.mongo.db.schools.find_one_or_404({'fragment': school},
                                         {'_id': True})
    c = mongo.SchoolCollections(school)
    term = c.term.find_one_or_404(
        {'fragment': term},
        {
            'id': True,
            'name': True,
            'start': True,
            'end': True,
            '_id': False,
        })
    counts = c.user.aggregate([
        # Keep only the relevant data
        {'$project': {
            'schedules.term': 1,
            'schedules.sections.id': 1,
            'schedules.sections.status': 1,
        }},
        # Split by term
        {'$unwind': '$schedules'},
        # Filter by term
        {'$match': {'schedules.term': term['id']}},
        # Split by section
        {'$unwind': '$schedules.sections'},
        # Group by section+status and count
        {'$group': {
            '_id': {
                'term': '$schedules.term',
                'section': '$schedules.sections.id',
                'status': '$schedules.sections.status'
            },
            'count': {'$sum': 1}
        }},
        # Move status & count into a subdocument
        {'$project': {
            'section': '$_id.section',
            'term': '$_id.term',
            'count': {'count': '$count', 'status': '$_id.status'},
            '_id': False,
        }},
        # Group by section, keeping list of count+status
        {'$group': {
            '_id': {
                'term': '$term',
                'section': '$section',
            },
            'counts': {'$push': '$count'},
        }},
        # Rename fields
        {'$project': {
            'term': '$_id.term',
            'section': '$_id.section',
            'counts': '$counts',
            '_id': 0,
        }},
        # Sort for output
        {'$sort': {'section': 1}},
    ])
    sections = list(c.course.aggregate([
        # Filter by term
        {'$match': {'term': term['id']}},
        # Drop unneeded data
        {'$project': {
            'name': 1,
            'code': 1,
            'fragment': 1,
            'sections.section': 1,
            'sections.id': 1,
            '_id': 0,
        }},
        # Split into sections
        {'$unwind': '$sections'},
        # Rename fields
        {'$project': {
            'course_name': '$name',
            'course_code': '$code',
            'course_fragment': '$fragment',
            'section': '$sections.section',
            'id': '$sections.id',
        }},
        # Sort for output
        {'$sort': {'id': 1}},
    ]))
    # Merge join
    cur_count = {'section': None}
    count_iter = iter(counts)
    has_more_counts = True
    zeros = {status: 0 for status in schedules.STATUSES}
    for section in sections:
        while has_more_counts and cur_count['section'] < section['id']:
            try:
                cur_count = count_iter.next()
            except StopIteration:
                has_more_counts = False
        if cur_count['section'] == section['id']:
            counts_by_status = {count['status']: count['count']
                                for count in cur_count['counts']}
            section.update({status: counts_by_status.get(status, 0)
                            for status in schedules.STATUSES})
        else:
            section.update(zeros)
        section['total'] = (
            section['maybe'] + section['definitely'] + section['official']
        )
    return sections


@routes.add('/api/student_interest/<school>/<term>')
def student_interest_json(school, term):
    data = student_interest_data(school, term)
    if isinstance(data, list):
        return flask.Response(json.dumps(data), mimetype='application/json')
    else:
        return data


CSV_FIELDS = ('course_code', 'section', 'course_name', 'maybe', 'definitely',
              'official', 'total', 'no')


@routes.add('/api/student_interest/<school>/<term>.csv')
def student_interest_csv(school, term):

    def row_to_csv(row):
        output = io.BytesIO()
        row = {
            key.encode('utf-8'):
            val.encode('utf-8') if isinstance(val, unicode) else val
            for key, val in row.iteritems()
        }
        writer = csv.DictWriter(output, CSV_FIELDS, extrasaction='ignore')
        writer.writerow(row)
        return output.getvalue()

    def generator(data):
        yield row_to_csv({
            'course_code': 'Course Code',
            'section': 'Section',
            'course_name': 'Course Name',
            'maybe': 'Interested',
            'definitely': 'Decided to Take',
            'official': 'Officially Enrolled',
            'total': 'Total Interest',
            'no': 'Ruled Out',
        })
        for row in data:
            yield row_to_csv(row)
    data = student_interest_data(school, term)
    if type(data) != list:
        # Must be some sort of error response
        return data
    response = flask.Response(generator(data), mimetype='text/csv')
    return response
