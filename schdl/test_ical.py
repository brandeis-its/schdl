from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import unittest

from schdl import test_data
from schdl.wsgi import app

class TestICal(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.maxDiff = None

    def test_ical(self):
        with test_data.Database.WithTestData() as data:
            response = self.app.get('/api/ical/testu/notagoodsecret')
        self.assertEqual(response.status_code, 200)
        expect = (
            'BEGIN:VCALENDAR\r\n'
            'VERSION:2.0\r\n'
            'PRODID:-//schdl/schdl//NONSGML v2.0//EN\r\n'
            'X-WR-CALDESC:Generated by Schdl\r\n'
            'X-WR-CALNAME;VALUE=TEXT:Schdl: John Q. Public\r\n'
            'X-WR-TIMEZONE:America/New_York\r\n'
            'BEGIN:VTIMEZONE\r\n'
            'TZID:America/New_York\r\n'
            'BEGIN:DAYLIGHT\r\n'
            'DTSTART;VALUE=DATE-TIME:20130310T020000\r\n'
            'TZNAME:EDT\r\n'
            'TZOFFSETFROM:-0500\r\n'
            'TZOFFSETTO:-0400\r\n'
            'END:DAYLIGHT\r\n'
            'BEGIN:STANDARD\r\n'
            'DTSTART;VALUE=DATE-TIME:20131103T020000\r\n'
            'TZNAME:EST\r\n'
            'TZOFFSETFROM:-0400\r\n'
            'TZOFFSETTO:-0500\r\n'
            'END:STANDARD\r\n'
            'END:VTIMEZONE\r\n'
            'BEGIN:VEVENT\r\n'
            'SUMMARY:BW101 1\r\n'
            'DTSTART;TZID=America/New_York;VALUE=DATE-TIME:20130121T100000\r\n'
            'DTEND;TZID=America/New_York;VALUE=DATE-TIME:20130121T105000\r\n'
            'DTSTAMP;VALUE=DATE-TIME:20120101T000000Z\r\n'
            'UID:bab0a1578f90981ad568deed544821979d656cb4@localhost\r\n'
            'CATEGORIES:CLASS\r\n'
            'DESCRIPTION:Introductory Basket Weaving\\n\\nInstructor: Tim J. Hickey\r\n'
            'RRULE:FREQ=WEEKLY;UNTIL=20130422T000000;BYDAY=MO,WE\r\n'
            'END:VEVENT\r\n'
            'END:VCALENDAR\r\n'
        )
        self.assertEqual(expect, response.data)
