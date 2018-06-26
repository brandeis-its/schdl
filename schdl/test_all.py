from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import sys
import unittest

from schdl import app
from schdl import test_browse
from schdl import test_ical
#from schdl import test_model
from schdl import test_schedules
from schdl import test_sessions
from schdl import test_static
from schdl import test_users
from schdl import test_util

suite = unittest.TestSuite()
test_modules = (
    test_browse,
    test_ical,
    # test_model,
    test_schedules,
    test_sessions,
    test_static,
    test_users,
    test_util,
)
for module in test_modules:
    suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(module))

if __name__ == '__main__':
    app.config.from_object('schdl.test_config')
    if not unittest.TextTestRunner().run(suite).wasSuccessful():
        sys.exit(1)
