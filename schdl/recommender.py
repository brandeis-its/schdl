from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import logging
import urllib
import urllib2

import flask
from flask import json
from flask import request

from schdl import app
from schdl import mongo
from schdl import util

LOGGER = logging.getLogger(__name__)

routes = util.RouteSet()


@routes.add('/api/recommender/<school>/<term>')
def recommender(school, term):
    if 'RECOMMENDER_URL' not in app.config:
        return flask.Response('[]', 'application/json')
    app.mongo.db.schools.find_one_or_404({'fragment': school},
                                         {'_id': True})
    c = mongo.SchoolCollections(school)
    term_obj = c.term.find_one_or_404(
        {'fragment': term}, {'_id': False, 'id': True})
    query = urllib.urlencode(
            [(key, val) for key, val in request.args.iteritems(multi=True)
                if key in ('course', 'exclude')])
    url = '{}?{}'.format(app.config['RECOMMENDER_URL'], query)
    LOGGER.debug('Requesting recommendations from %s', url)
    result = urllib2.urlopen(url)
    try:
        continuity_ids = json.load(result)['recommendations']
    finally:
        result.close()
    LOGGER.debug('Got %s courses', len(continuity_ids))
    courses = list(c.course.find(
        {
            'continuity_id': {'$in': continuity_ids},
            'term': term_obj['id'],
        },
        util.project_course_for_search.mongo()
    ))
    # TODO: sort by recommended order
    LOGGER.debug('Found %s courses in term %s', len(courses), term)
    return flask.Response(json.dumps(courses), mimetype='application/json')
