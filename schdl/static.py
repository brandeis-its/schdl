from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import flask

from schdl import app
from schdl import util

routes = util.RouteSet()


@routes.add('/robots.txt')
def robotstxt():
    return flask.send_file('robots.txt')


@routes.add('/')
def htmlfile(path=None):
    return app.send_static_file('index.html')

routes.append('/<path:path>', endpoint='htmlfile', view_func=htmlfile)
