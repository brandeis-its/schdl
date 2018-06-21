from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import unittest

from schdl import util


class TestUtil(unittest.TestCase):
    def test_name(self):
        user = {'first': None, 'middle': None, 'last': None}
        self.assertEqual('', util.name(user))
        user['first'] = 'John'
        self.assertEqual('John', util.name(user))
        user['last'] = 'Public'
        self.assertEqual('John Public', util.name(user))
        user['middle'] = 'Q.'
        self.assertEqual('John Q. Public', util.name(user))
        user['last'] = None
        self.assertEqual('John Q.', util.name(user))
        user['first'] = ''
        self.assertEqual('Q.', util.name(user))
        user['middle'] = None
        user['last'] = 'Public'
        self.assertEqual('Public', util.name(user))

# TODO(eitan): add tests
#    def test_formatCourseSection(self):


class TestUser(unittest.TestCase):
    pass  # TODO(eitan): add tests
