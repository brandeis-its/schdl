#!/usr/bin/env python2.7

from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import logging

from werkzeug.contrib.profiler import ProfilerMiddleware

from schdl.wsgi import app

app.wsgi_app = ProfilerMiddleware(app.wsgi_app, profile_dir='/tmp/schdl_prof')


def main():
    logging.basicConfig(level=logging.INFO)
    app.run()


if __name__ == '__main__':
    main()
