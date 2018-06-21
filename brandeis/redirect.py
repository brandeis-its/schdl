from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import logging

import flask

from schdl import util

LOGGER = logging.getLogger(__name__)

app = flask.Flask(__name__)
app.config.from_object('schdl.baseconfig')
app.config.from_pyfile('../schdl.cfg')

routes = util.RouteSet()


def redirect(suffix):
    return flask.redirect(app.config['BRANDEIS_DST_HOST'] + suffix, code=301)


@routes.add('/brandeis/term/<term>/search')
def search_term(term):
    return redirect('/search?term=' + term)


@routes.add('/brandeis/course/<term>/<course>')
def browse_course(term, course):
    return redirect('/course/%s/%s' % (term, course))


@routes.add('/brandeis/subject/<term>/<subject>')
def browse_subject(term, subject):
    # Most subjects' fragments have changed - redirect to term page
    return redirect('/term/%s' % term)


@routes.add('/brandeis/term/<term>')
def browse_term(term):
    return redirect('/term/%s' % term)


@routes.add('/brandeis/instructor/<instr>')
def browse_instructor(instr):
    return redirect('/instructor/%s' % instr)


@routes.add('/brandeis/browse')
@routes.add('/', endpoint='welcome')
@routes.add('/login', endpoint='login')
def browse_school(path=None):
    return redirect('/')


@routes.add('/schedule/brandeis/<term>')
@routes.add('/schedule/brandeis/<term>/print', endpoint='schedule_view_print')
def schedule_view(term):
    return redirect('/schedule/%s' % term)


@routes.add('/user/<user>/schedule/brandeis/<term>/<secret>')
@routes.add('/user/<user>/schedule/brandeis/<term>/<secret>/print',
            endpoint='shared_schedule_print')
def shared_schedule(user, term, secret):
    return redirect('/schedule/%s/%s' % (term, secret))


@routes.add('/user/<user>/ical')
def user_ical(user):
    secret = flask.request.args.get('key')
    if secret is None:
        flask.abort(404)
    return redirect('/api/ical/brandeis/%s' % secret)


@routes.add('/login/<path:redirect>')
def login_redirect(redirect):
    return flask.redirect('/' + redirect)

# Catch-all
routes.append('/<path:path>', endpoint='catchall', view_func=browse_school)

routes.apply(app)


class HostBasedRouter(object):
    def __init__(self, host, app, other_app):
        self.host = host
        self.app = app
        self.other_app = other_app

    def __call__(self, environ, start_response):
        if environ.get('HTTP_HOST') == self.host:
            return self.app(environ, start_response)
        else:
            return self.other_app(environ, start_response)
