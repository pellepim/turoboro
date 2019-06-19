import unittest
from datetime import datetime
import turoboro.common


class IsIsoDatetimeTest(unittest.TestCase):
    def test(self):
        self.assertRaises(ValueError, turoboro.common.is_iso_datetime, '2012-01-01T12:32:01.3829834')
        self.assertRaises(ValueError, turoboro.common.is_iso_datetime, '2012-01-01 12:32:01')


class IsListOfDaysTest(unittest.TestCase):
    def test(self):
        # Invalid day
        self.assertRaises(ValueError, turoboro.common.is_list_of_days, (-1,))
        # Too many days
        self.assertRaises(ValueError, turoboro.common.is_list_of_days, turoboro.DAYS + (turoboro.MONDAY,))
        # Invalid data type
        self.assertRaises(ValueError, turoboro.common.is_list_of_days, '0,1,2')
        # Success
        self.assertEqual(
            (turoboro.MONDAY, turoboro.THURSDAY),
            turoboro.common.is_list_of_days((turoboro.MONDAY, turoboro.THURSDAY))
        )


class IsListOfMonthsTest(unittest.TestCase):
    def test(self):
        # Invalid Month
        self.assertRaises(ValueError, turoboro.common.is_list_of_months, (0,))
        # Too many months
        self.assertRaises(ValueError, turoboro.common.is_list_of_months, turoboro.MONTHS + (turoboro.JANUARY,))
        # Invalid data type
        self.assertRaises(ValueError, turoboro.common.is_list_of_months, '1, 2, 3')
        # Success
        self.assertEqual(
            (turoboro.MARCH, turoboro.SEPTEMBER, turoboro.JANUARY),
            turoboro.common.is_list_of_months((turoboro.MARCH, turoboro.SEPTEMBER, turoboro.JANUARY))
        )
