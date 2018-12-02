#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Suite of unit-tests for testing get_datetime function
"""

# This Source Code Form is subject to the terms of the
# Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import unittest

import pomolight as pl

class TestGetDatetime(unittest.TestCase):

    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)

        self.now = datetime.datetime(2018, 4, 30, 19, 13, 36)

    def test_delta_hours(self):
        self.assertEqual(datetime.datetime(2018, 4, 30, 21, 13, 36), pl.get_datetime(self.now, "+2h"))
        self.assertEqual(datetime.datetime(2018, 4, 30, 20, 13, 36), pl.get_datetime(self.now, "+1h"))
        self.assertEqual(datetime.datetime(2018, 4, 30, 19, 43, 36), pl.get_datetime(self.now, "+0.5h"))

    def test_delta_minutes(self):
        self.assertEqual(datetime.datetime(2018, 4, 30, 19, 15, 36), pl.get_datetime(self.now, "+2m"))
        self.assertEqual(datetime.datetime(2018, 4, 30, 19, 14, 36), pl.get_datetime(self.now, "+1m"))
        self.assertEqual(datetime.datetime(2018, 4, 30, 19, 14, 6), pl.get_datetime(self.now, "+0.5m"))

    def test_delta_seconds(self):
        self.assertEqual(datetime.datetime(2018, 4, 30, 19, 13, 38), pl.get_datetime(self.now, "+2s"))
        self.assertEqual(datetime.datetime(2018, 4, 30, 19, 13, 37), pl.get_datetime(self.now, "+1s"))

    def test_delta_full(self):
        self.assertEqual(datetime.datetime(2018, 4, 30, 19, 28, 36), pl.get_datetime(self.now, "+15"))
        self.assertEqual(datetime.datetime(2018, 4, 30, 19, 29, 6), pl.get_datetime(self.now, "+15:30"))
        self.assertEqual(datetime.datetime(2018, 4, 30, 20, 29, 6), pl.get_datetime(self.now, "+1:15:30"))
        self.assertEqual(datetime.datetime(2018, 4, 30, 19, 14, 6), pl.get_datetime(self.now, "+:30"))
        self.assertEqual(datetime.datetime(2018, 4, 30, 19, 28, 36), pl.get_datetime(self.now, "+15:"))
        self.assertEqual(datetime.datetime(2018, 4, 30, 20, 13, 36), pl.get_datetime(self.now, "+1::"))

    def test_abs_minutes(self):
        self.assertEqual(datetime.datetime(2018, 4, 30, 20, 0, 0), pl.get_datetime(self.now, ":00"))
        self.assertEqual(datetime.datetime(2018, 4, 30, 19, 20, 0), pl.get_datetime(self.now, ":20"))
        self.assertEqual(datetime.datetime(2018, 4, 30, 20, 0, 0), pl.get_datetime(self.now, "00"))

    def test_abs_hours_minutes(self):
        self.assertEqual(datetime.datetime(2018, 4, 30, 20, 0, 0), pl.get_datetime(self.now, "20:00"))
        self.assertEqual(datetime.datetime(2018, 4, 30, 20, 30, 0), pl.get_datetime(self.now, "20:30"))

    def test_abs_full(self):
        self.assertEqual(datetime.datetime(2018, 4, 30, 19, 14, 0), pl.get_datetime(self.now, "::00"))
        self.assertEqual(datetime.datetime(2018, 4, 30, 19, 20, 0), pl.get_datetime(self.now, ":20:"))
        self.assertEqual(datetime.datetime(2018, 4, 30, 20, 0, 0), pl.get_datetime(self.now, "20::"))
        self.assertEqual(datetime.datetime(2018, 4, 30, 20, 30, 15), pl.get_datetime(self.now, "20:30:15"))

if __name__ == '__main__':
    unittest.main()
