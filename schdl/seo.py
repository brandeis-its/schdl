from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import datetime
import io
import json
import logging
import math
import urlparse

import flask

from angular2tmpl import jinja2
from angular2tmpl import module

from schdl import app
from schdl import browse
from schdl import util

LOGGER = logging.getLogger(__name__)

routes = util.RouteSet()


class EscapedFragmentRedirector(object):
    """WSGI middleware: redirect if _escaped_fragment_ in query string."""
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        qs = urlparse.parse_qs(environ['QUERY_STRING'], True)
        if '_escaped_fragment_' in qs:
            environ['PATH_INFO'] = '/_static' + environ['PATH_INFO']
        return self.app(environ, start_response)


def _render_template(tmpl, data):
    return flask.render_template(tmpl, **jinja2.js_data(data))


# TODO(eitan): avoid import side-effects!
app.wsgi_app = EscapedFragmentRedirector(app.wsgi_app)


def _get_json_data(response):
    data = json.loads(flask.make_response(response).get_data())
    LOGGER.debug('Got template data: %r', data)
    return data


ROUTES = {
    'school': 'generated/app/school/school.tpl.html',
    'search': 'generated/app/search/search.tpl.html',
    'term': 'generated/app/term/term.tpl.html',
    'subject': 'generated/app/subject/subject.tpl.html',
    'course': 'generated/app/course/course.tpl.html',
    'instructor': 'generated/app/instructor/instructor.tpl.html',
    'privacy': 'generated/app/privacy/privacy.tpl.html',
    'terms': 'generated/app/terms/terms.tpl.html',
}


def _get_school_data():
    if 'force_host' in flask.request.args:
        host = flask.request.args['force_host']
    else:
        host = flask.request.host
        if ':' in host:
            host = host.split(':')[0]
    school = _get_json_data(browse.schoolByHostName(host))
    school['past'] = []
    school['current'] = []
    school['future'] = []
    # TODO(eitan): Use school's timezone
    today = datetime.date.today().strftime('%Y%m%d')
    for term in school['terms']:
        if term['start'] <= today:
            if term['end'] >= today:
                school['current'].append(term)
            else:
                school['past'].append(term)
        else:
            school['future'].append(term)
    return school


def getRoutes(server_side_links):
    suffix = '?_escaped_fragment_&force' if server_side_links else ''
    return {
        'School': lambda school: '/%s' % suffix,
        'Term': lambda school, term: '/term/%s%s' % (term, suffix),
        'Subject': (
            lambda school, term, subject:
            '/subject/%s/%s%s' % (term, subject, suffix)
        ),
        'Course': (
            lambda school, term, course:
            '/course/%s/%s%s' % (term, course, suffix)
        ),
        'Instructor': (
            lambda school, instructor:
            '/instructor/%s%s' % (instructor, suffix)
        ),
    }


@routes.add('/_static/')
def static_school(path=None):
    school = _get_school_data()
    tmpl_data = {
        'title': '%s Course Listings' % school['name'],
        'school': school,
        'Routes': getRoutes('force' in flask.request.args),
        'ngViewRoutes': ROUTES,
        'ngViewRoute': 'school',
    }
    return _render_template('generated/index.html', tmpl_data)


@routes.add('/_static/search')
def static_search():
    school = _get_school_data()
    tmpl_data = {
        'title': 'Search',
        'school': school,
        'Routes': getRoutes('force' in flask.request.args),
        'ngViewRoutes': ROUTES,
        'ngViewRoute': 'search',
    }
    return _render_template('generated/index.html', tmpl_data)


@routes.add('/_static/term/<term>')
def static_term(term):
    school = _get_school_data()
    term = _get_json_data(browse.term(school['fragment'], term))
    tmpl_data = {
        'title': term['name'],
        'school': school,
        'term': term,
        'Routes': getRoutes('force' in flask.request.args),
        'ngViewRoutes': ROUTES,
        'ngViewRoute': 'term',
    }
    return _render_template('generated/index.html', tmpl_data)


@routes.add('/_static/subject/<term>/<subject>')
def static_subject(term, subject):
    school = _get_school_data()
    subject = _get_json_data(browse.subject(school['fragment'], term, subject))
    reqs = {req['id']: req for req in school['requirements']}
    for seg in subject['segments']:
        for course in seg['courses']:
            course['requirements'] = [reqs[req]
                                      for req in course['requirements']]
    tmpl_data = {
        'title': '%s - %s' % (subject['name'], subject['term']['name']),
        'school': school,
        'subject': subject,
        'Routes': getRoutes('force' in flask.request.args),
        'ngViewRoutes': ROUTES,
        'ngViewRoute': 'subject',
    }
    return _render_template('generated/index.html', tmpl_data)


@routes.add('/_static/course/<term>/<course>')
def static_course(term, course):
    school = _get_school_data()
    course = _get_json_data(browse.course(school['fragment'], term, course))
    reqs = {req['id']: req for req in school['requirements']}
    course['requirements'] = [reqs[req] for req in course['requirements']]
    exists = lambda x: not (x is None
                            or isinstance(x, app.jinja_env.undefined))
    tmpl_data = {
        'title': '%s: %s - %s' % (
            course['code'], course['name'], course['term']['name']),
        'school': school,
        'course': course,
        'exists': exists,
        'Routes': getRoutes('force' in flask.request.args),
        'ngViewRoutes': ROUTES,
        'ngViewRoute': 'course',
    }
    return _render_template('generated/index.html', tmpl_data)


@routes.add('/_static/instructor/<instructor>')
def static_instructor(instructor):
    school = _get_school_data()
    instructor = _get_json_data(
        browse.instructor(school['fragment'], instructor))
    tmpl_data = {
        'title': instructor['name'],
        'school': school,
        'instructor': instructor,
        'Routes': getRoutes('force' in flask.request.args),
        'ngViewRoutes': ROUTES,
        'ngViewRoute': 'instructor',
    }
    return _render_template('generated/index.html', tmpl_data)


@routes.add('/_static/privacy')
def static_privacy():
    school = _get_school_data()
    tmpl_data = {
        'title': 'Privacy Policy',
        'school': school,
        'Routes': getRoutes('force' in flask.request.args),
        'ngViewRoutes': ROUTES,
        'ngViewRoute': 'privacy',
    }
    return _render_template('generated/index.html', tmpl_data)


@routes.add('/_static/terms')
def static_terms():
    school = _get_school_data()
    tmpl_data = {
        'title': 'Terms and Conditions',
        'school': school,
        'Routes': getRoutes('force' in flask.request.args),
        'ngViewRoutes': ROUTES,
        'ngViewRoute': 'terms',
    }
    return _render_template('generated/index.html', tmpl_data)


def columns_filter(items, cols, min):
    n = len(items)
    if n < min:
        return [items]
    x = int(math.ceil(n / cols))
    return [items[i * x: i * x + x] for i in xrange(cols)]

app.jinja_env.filters['columns'] = columns_filter


schdl_mod = module.Module('schdl')


@schdl_mod.directive(
    restrict='E',
    templatePath='/static/course/sectionStatus.tpl.html',
    scope={
        'status': '=',
        'statusText': '=',
        'enrolled': '=',
        'limit': '=',
        'waiting': '=',
    },
)
def schdlSectionStatus(document, element):
    pass


@schdl_mod.filter()
def schdlDays(days):
    DAY_NAMES = {
        'su': 'Su',
        'm': 'M',
        'tu': 'Tu',
        'w': 'W',
        'th': 'Th',
        'f': 'F',
        'sa': 'Sa',
    }
    DAYS = ['su', 'm', 'tu', 'w', 'th', 'f', 'sa']
    out = io.StringIO()
    for day in DAYS:
        if day in days:
            out.write(DAY_NAMES[day])
    return out.getvalue()


@schdl_mod.filter()
def schdlTime(time):
    hours = time // 60
    minutes = time % 60
    if hours >= 12:
        ampm = 'PM'
        if hours > 12:
            hours -= 12
    else:
        ampm = 'AM'
        if hours == 0:
            hours = 12
    return '%s:%s %s' % (hours, minutes, ampm)


# TODO(eitan): import side-effect
schdl_mod.apply_to_jinja_env(app.jinja_env)


heads = module.Module('heads')


@heads.directive(restrict='E')
def head(document, element):
    if not element.getElementsByTagName('title'):
        title = document.createElement('title')
        title.appendChild(document.createTextNode('{{title}}'))
        element.appendChild(title)


routes.append('/_static/<path:path>', endpoint='static_catchall',
              view_func=static_school)
