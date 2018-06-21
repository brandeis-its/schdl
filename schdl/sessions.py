from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import datetime

from flask import jsonify
from flask import request
from flask.ext import login
from bson import objectid

from schdl import app
from schdl import mongo
from schdl import users
from schdl import util

routes = util.RouteSet()


@app.login_manager.user_loader
def load_user(user_id):
    try:
        school, user_id = user_id.split(':', 1)
    except ValueError:
        return None
    try:
        user_id = objectid.ObjectId(user_id)
    except objectid.InvalidId:
        return None
    school = app.mongo.db.schools.find_one({'fragment': school})
    c = mongo.SchoolCollections(school['fragment'])
    user = c.user.find_one({'_id': user_id})
    if user:
        return util.User(user, school)


@app.login_manager.unauthorized_handler
def unauthorized():
    return jsonify(status='login'), 403


@routes.add('/api/session/<school>', methods=['POST'])
def user_login(school):
    school = app.mongo.db.schools.find_one({'fragment': school})
    c = mongo.SchoolCollections(school['fragment'])
    email = request.json['email']
    password = request.json['password']
    user = c.user.find_one({'email':  email})
    if user is None:
        return jsonify(reason='noaccount'), 403
    if app.bcrypt.check_password_hash(user['passhash'], password):
        if login.login_user(util.User(user, school)):
            c.user.update({
                '_id': user['_id']
            }, {
                '$set': {'last_login': datetime.datetime.utcnow()},
            })
            return users.current_user()
        else:
            return jsonify(reason='unverified'), 403
    else:
        return jsonify(reason='password'), 403


@routes.add('/api/session', methods=['DELETE'])
def logout():
    login.logout_user()
    return jsonify(status='ok')
