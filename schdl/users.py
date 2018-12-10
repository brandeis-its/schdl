from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import datetime
import logging

import flask
import flask_login
import flask_mail
import pymongo

from schdl import app
from schdl import mongo
from schdl import util


LOGGER = logging.getLogger(__name__)

routes = util.RouteSet()


def addInstructorCourses(c, user, term=None):
    instructors = c.instructor.find({'email': {'$in': user['email']}})
    schs = {sch['term']: sch for sch in user['schedules']}
    for instr in instructors:
        query = {'sections.instructors': instr['id']}
        if term is not None:
            query['term'] = term
        courses = c.course.find(
            query,
            {
                'term': True,
                'sections': True,
                '_id': False,
            }
        )
        for course in courses:
            sections = [sect for sect in course['sections']
                        if instr['id'] in sect['instructors']]
            if course['term'] not in schs:
                schs[course['term']] = {
                    'term': course['term'],
                    'sections': [],
                }
                user['schedules'].append(schs[course['term']])
            for sect in sections:
                schs[course['term']]['sections'].append({
                    'status': 'instructor',
                    'id': sect['id'],
                })


@routes.add('/api/user', methods=['GET'])
def current_user():
    # TODO(eitan): optimize!
    user = flask_login.current_user
    if user.is_anonymous:
        return 'null'
    c = mongo.SchoolCollections(user.school['fragment'])
    addInstructorCourses(c, user)
    schedules = user.formatSchedules()
    roles = {role: True for role in user['roles']}
    return flask.jsonify(name=user.name(),
                         first=user['first'],
                         middle=user['middle'],
                         last=user['last'],
                         email=user['email'],
                         schedules=schedules,
                         roles=roles,
                         secret=user['secret'])


@routes.add('/api/user', methods=['POST'])
@flask_login.login_required
def update_user():
    user = flask_login.current_user
    c = mongo.SchoolCollections(user.school['fragment'])
    update = {}
    request = flask.request.json
    does_something = False
    for part in ('first', 'middle', 'last'):
        if part in request and request[part] != user[part]:
            if not isinstance(request[part], unicode):
                raise ValueError('Invalid type for request arg %s' % part)
            does_something = True
            update.setdefault('$set', {})
            update['$set'][part] = request[part]
    if 'add_email' in request and isinstance(request['add_email'], unicode):
        email_in_use = c.user.find_one({'email': request['add_email']},
                                       {'_id': True})
        if email_in_use:
            return flask.jsonify(status='email_in_use'), 409  # Conflict
        ttl = datetime.timedelta(days=30)
        secret = util.create_verification(c, 'add_email', ttl=ttl,
                                          user=user['_id'],
                                          email=request['add_email'])
        msg = flask_mail.Message(
            "Confirm Your Email Address",
            recipients=[request['add_email']],
        )
        msg.html = flask.render_template(
            'email/verify_new_email.html',
            school=user.school,
            user=user,
            secret=secret,
            email=request['add_email'],
        )
        msg.body = flask.render_template(
            'email/verify_new_email.txt',
            school=user.school,
            user=user,
            secret=secret,
            email=request['add_email'],
        )
        app.mail.send(msg)
        does_something = True
    if ('primary_email' in request
            and request['primary_email'] != user['email'][0]):
        # Don't allow deleting former primary address, to match semantics of
        # stand-along delete_email. If attempting to deleting an address and
        # set it as primary, ignore the delete and just make it primary.
        new_emails = [email for email in user['email'][1:]
                      if email == request['primary_email']
                      or email not in request.get('delete_email', [])]
        new_emails = user['email'][0:1] + new_emails
        new_emails.remove(request['primary_email'])
        new_emails = [request['primary_email']] + new_emails
        update.setdefault('$set', {})
        update['$set']['email'] = new_emails
        does_something = True
    elif 'delete_email' in request:
        delete_emails = [email for email in request['delete_email']
                         if email in user['email'][1:]]
        if delete_emails:
            update['$pull'] = {'email': {'$in': delete_emails}}
            does_something = True
    if 'old_password' in request and 'new_password' in request:
        if app.bcrypt.check_password_hash(user['passhash'],
                                          request['old_password']):
            update.setdefault('$set', {})
            update['$set']['passhash'] = app.bcrypt.generate_password_hash(
                request['new_password'])
            does_something = True
        else:
            return flask.jsonify(status='password_incorrect'), 403
    if does_something:
        if update:
            c.user.update({'_id': user['_id']}, update, w=1)
        return flask.jsonify(status='success')
    else:
        return flask.jsonify(status='noop')


@routes.add('/api/user/<school>', methods=['POST'])
def register(school):
    # If logged in, just return current user
    if not flask_login.current_user.is_anonymous:
        return current_user()
    request = flask.request.json
    school = app.mongo.db.schools.find_one_or_404(
        {'fragment': school},
        {'_id': False})
    c = mongo.SchoolCollections(school['fragment'])
    email_in_use = c.user.find_one({'email': request['email']})
    if email_in_use:
        return flask.jsonify(), 409  # Conflict
    user = util.User({
        'first': request['first'],
        'middle': '',
        'last': request['last'],
        'email': [request['email']],
        'schedules': [],
        'secret': util.generate_secret(),
        'roles': [],
    }, school)
    user.set_password(request['password'])
    ttl = datetime.timedelta(days=1)
    secret = util.create_verification(c, 'new_user', user=user.user, ttl=ttl)
    user['name'] = user.name()
    msg = flask_mail.Message(
        "Confirm Your Email Address",
        # User must have exactly one email address at account creation
        recipients=user['email'],
    )
    msg.html = flask.render_template(
        'email/new_user_verify_email.html',
        school=school,
        user=user.user,
        secret=secret,
    )
    msg.body = flask.render_template(
        'email/new_user_verify_email.txt',
        school=school,
        user=user.user,
        secret=secret,
    )
    app.mail.send(msg)
    return flask.jsonify()


@routes.add('/api/reset_password/<school>', methods=['POST'])
def reset_password(school):
    request = flask.request.json
    school = app.mongo.db.schools.find_one_or_404(
        {'fragment': school},
        {'_id': False})
    c = mongo.SchoolCollections(school['fragment'])
    user = c.user.find_one_or_404({
        'email': request['email'],
    }, {
        '_id': True,
        'email': True,
        'first': True,
        'middle': True,
        'last': True,
    })
    user = util.User(user, school)
    user['name'] = user.name()
    secret = util.create_verification(c, 'reset_password', user=user['_id'])
    msg = flask_mail.Message(
        "Password Reset",
        recipients=user['email'][0:1],
    )
    msg.html = flask.render_template(
        'email/reset_password.html',
        school=school,
        user=user.user,
        secret=secret,
    )
    msg.body = flask.render_template(
        'email/reset_password.txt',
        school=school,
        user=user.user,
        secret=secret,
    )
    app.mail.send(msg)
    return flask.jsonify()


@routes.add('/api/verify/<school>', methods=['POST'])
def verify(school):
    request = flask.request.json
    school = app.mongo.db.schools.find_one_or_404(
        {'fragment': school},
        {'_id': False})
    c = mongo.SchoolCollections(school['fragment'])
    verification = c.email_verification.find_one_or_404({
        'secret': request['secret'],
    })
    type_ = verification['type']
    # Check that it's still valid
    if verification.get('used'):
        return flask.jsonify(type=type_, status='used')
    elif (verification['expiration'].replace(tzinfo=None)
          < datetime.datetime.utcnow()):
        return flask.jsonify(type=type_, status='expired')
    if type_ == 'new_user':
        try:
            c.user.insert(verification['user'], w=1)
        except pymongo.errors.DuplicateKeyError:
            return flask.jsonify(type=type_, status='account_exists')
    elif type_ == 'reset_password':
        if 'password' not in request:
            return flask.jsonify(type=type_, status='need_password')
        user = util.User({}, school)
        user.set_password(request['password'])
        c.user.update({
            '_id': verification['user'],
        }, {
            '$set': {'passhash': user['passhash']},
        }, w=1)
    elif type_ == 'add_email':
        c.user.update({
            '_id': verification['user'],
        }, {
            '$addToSet': {'email': verification['email']}
        })
    else:
        raise ValueError('Unknown verification type %s' % type_)
    c.email_verification.update({
        '_id': verification['_id'],
    }, {
        '$set': {'used': True},
    })
    return flask.jsonify(type=type_, status='success')


@routes.add('/api/user/<school>', methods=['GET'])
def shared_schedule(school):
    """Get a user by the secret on one of their schedules and return just
    that schedule's info."""
    school = app.mongo.db.schools.find_one_or_404(
        {'fragment': school},
        {'_id': False})
    c = mongo.SchoolCollections(school['fragment'])
    user = util.User(c.user.find_one_or_404(
        {'schedules.secret': flask.request.args['secret']},
        {
            'email': True,  # For linking to instructors - do not print
            'first': True,
            'middle': True,
            'last': True,
            'schedules.$': True,
        },
    ), school)
    sch = user['schedules'][0]
    sch['sections'] = [sect for sect in sch['sections']
                       if sect['status'] != 'no']
    addInstructorCourses(c, user, term=sch['term'])
    schedules = user.formatSchedules()
    return flask.jsonify(name=user.name(), schedules=schedules)
