from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import os
import unittest

import schdl

from schdl.wsgi import app


class TestStaticFiles(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_index(self):
        src_path = os.path.join(app.static_folder, 'index.html')
        with open(src_path) as src:
            src_data = src.read()
        for path in ('/', '/testu/browse'):
            response = self.app.get(path)
            self.assertEqual(response.data, src_data)

    def test_static(self):
        src_path = os.path.join(app.static_folder, 'index.html')
        with open(src_path) as src:
            src_data = src.read()
        response = self.app.get('/static/index.html')
        self.assertEqual(response.data, src_data)


if __name__ == '__main__':
    app.config.from_object('schdl.test_config')
    unittest.main()
