from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

from brandeis import redirect

from schdl import app
from schdl import users
from schdl import sessions
from schdl import browse
from schdl import schedules
from schdl import registrar
from schdl import ical
from schdl import recommender
from schdl import updates
from schdl import static


MODULES = (
    users,
    sessions,
    browse,
    schedules,
    ical,
    updates,
    registrar,
    recommender,
    static,  # static *must* be last because it includes the catch-all
)

# *import side-effect* - applies routing to the app
for module in MODULES:
    module.routes.apply(app)


# *import side-effect* - applies middleware to the app
app.wsgi_app = redirect.HostBasedRouter(app.config['BRANDEIS_SRC_HOST'],
                                        redirect.app,
                                        app.wsgi_app)
