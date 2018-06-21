from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import unittest

from schdl import test_data
from schdl.wsgi import app


class TestIndex(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_redirect(self):
        with test_data.Database.WithTestData() as data:
            response = self.app.get('http://%s/?_escaped_fragment_'
                                    % data.school['hostname'][0])
        self.assertEqual(response.status_code, 200)
        # TODO(eitan): assert something about the output

if __name__ == '__main__':
    app.config.from_object('schdl.test_config')
    unittest.main()
