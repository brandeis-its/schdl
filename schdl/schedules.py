from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import datetime

import flask
from flask import request

from flask.ext import login

from schdl import app
from schdl import mongo
from schdl import users
from schdl import util

STATUSES = ('maybe', 'definitely', 'official', 'no')

routes = util.RouteSet()


@routes.add('/api/schedules/<school>/<term>/<section>',
            methods=['PUT', 'DELETE'])
@login.login_required
def update_schedule(school, term, section):
    section = util.decode_section_id(section)
    user = login.current_user
    app.mongo.db.schools.find_one_or_404({'fragment': school},
                                         {'_id': True})
    c = mongo.SchoolCollections(school)
    term = c.term.find_one_or_404({'fragment': term},
                                  {'_id': False})
    schedule = util.getSchedule(user, term['id'])
    if schedule:
        new_schedule = False
    else:
        schedule = {
            'term': term['id'],
            'sections': [],
            'updated': datetime.datetime.utcnow(),
            'secret': util.generate_secret(),
        }
        new_schedule = True
    if request.method == 'DELETE':
        schedule_section = util.getScheduleCourseSection(schedule, section)
        if schedule_section:
            # Update local copy
            schedule['sections'].remove(schedule_section)
            # Delete only if exists
            delete_schedule_section(user['_id'], school,
                                    term['id'], section)
    else:
        status = request.get_json()['status']
        if status not in STATUSES:
            return flask.jsonify(reason='invalid_status'), 400
        c.course.find_one_or_404(
            {'sections.id': section}, {'_id': 1})
        if new_schedule:
            schedule_section = {
                'id': section,
                'status': status,
                'updated': datetime.datetime.utcnow(),
            }
            # Schedule does not exist - create it
            schedule['sections'].append(schedule_section)
            # Update local copy
            user['schedules'].append(schedule)
            c.user.update(
                {'_id': user['_id']},
                {'$push': {'schedules': schedule}}
            )
        else:
            # Schedule exists - is section in it?
            schedule_section = util.getScheduleCourseSection(schedule, section)
            if schedule_section:
                # Section is in schedule - update it if necessary
                if schedule_section['status'] != status:
                    # Update local copy (also used for remote update)
                    schedule_section['status'] = status
                    schedule_section['updated'] = datetime.datetime.utcnow()
                    # delete and add because atomic update is not available:
                    # https://jira.mongodb.org/browse/SERVER-831
                    delete_schedule_section(user['_id'], school,
                                            term['id'], section)
                    add_schedule_section(user['_id'], school,
                                         term['id'], schedule_section)
            else:
                # Section is not in schedule - add it
                schedule_section = {
                    'id': section,
                    'status': status,
                    'updated': datetime.datetime.utcnow(),
                }
                # Update local copy
                schedule['sections'].append(schedule_section)
                add_schedule_section(user['_id'], school,
                                     term['id'], schedule_section)
    return users.current_user()


def delete_schedule_section(user_id, school_id, term_id, section_id):
    c = mongo.SchoolCollections(school_id)
    return c.user.update(
        {
            '_id': user_id,
            'schedules.term': term_id,
        }, {
            '$set': {'schedules.$.updated': datetime.datetime.utcnow()},
            '$pull': {'schedules.$.sections': {'id': section_id}},
        }
    )


def add_schedule_section(user_id, school_id, term_id, schedule_section):
    c = mongo.SchoolCollections(school_id)
    return c.user.update(
        {
            '_id': user_id,
            'schedules.term': term_id,
        },
        {
            '$set': {'schedules.$.updated': datetime.datetime.utcnow()},
            '$push': {'schedules.$.sections': schedule_section},
        }
    )
