from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

from schdl.wsgi import app
from schdl import testing_routes

# TODO(eitan): this will not work because the catch-all comes first
testing_routes.routes.apply(app)
