from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import flask

from schdl import app
from schdl import util

routes = util.RouteSet()


@routes.add('/test/<path:filename>')
def test_static(filename=None):
    return flask.send_from_directory(app.root_path + '/../ui/test/', filename)
