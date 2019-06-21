import unittest
import turoboro.rules
import turoboro.common
from datetime import datetime
import voluptuous
import itertools


class DailyRuleSetupTests(unittest.TestCase):
    def setUp(self):
        self.starting_point = turoboro.common.datetime_from_isoformat('2014-01-01T00:00:00')
        self.daily_rule = turoboro.rules.DailyRule(self.starting_point)

    def test_default_spec(self):
        expected = {
            'exceptDays': None,
            'exceptMonths': None,
            'hour': 0,
            'repeat': 1,
            'rule': 'daily',
            'start': '2014-01-01T00:00:00',
            'end': None
        }

        self.assertEqual(self.daily_rule.spec, expected)

    def test_repeat(self):
        self.assertRaises(voluptuous.MultipleInvalid, self.daily_rule.repeat, 0)
        self.assertRaises(voluptuous.MultipleInvalid, self.daily_rule.repeat, 8)
        for repeat in range(2, 8):
            self.daily_rule.repeat(repeat)
            self.assertEqual(self.daily_rule.spec['repeat'], repeat)
        self.assertEqual(self.daily_rule, self.daily_rule.repeat(1))

    def test_except_days(self):
        """
        There are 126 valid ways in which to specify days of the week on which to NOT do something. We cannot
        allow to except all 7 days from the rule - because then what would be the use of the rule?
        """
        # Set up all combinations of days of weeks that are at least ONE day and at the most SIX.
        valid_combination_sets = [list(itertools.combinations(turoboro.DAYS, n)) for n in range(1, 7)]
        combination_count = 0
        for valid_combinations_in_range in valid_combination_sets:
            for combination in valid_combinations_in_range:
                combination_count += 1
                self.daily_rule.except_days(combination)
                self.assertEqual(self.daily_rule.spec['exceptDays'], combination)

        self.assertEqual(combination_count, 126)

        # Lets try some invalids
        self.assertRaises(voluptuous.MultipleInvalid, self.daily_rule.except_days, (-1,))
        self.assertRaises(voluptuous.MultipleInvalid, self.daily_rule.except_days, (7,))
        # We cannot allow all the days of the week to be excluded from the rule
        self.assertRaises(voluptuous.MultipleInvalid, self.daily_rule.except_days, turoboro.DAYS)

    def test_except_months(self):
        """
        There are 4094 valid ways in which to specify months of the year on which to NOT do something.
        We cannot allow to except all 12 months from the rule - because then what would be the use of the rule?
        """
        valid_combination_sets = [list(itertools.combinations(turoboro.MONTHS, n)) for n in range(1, 12)]
        combination_count = 0
        for valid_combinations_in_range in valid_combination_sets:
            for combination in valid_combinations_in_range:
                combination_count += 1
                self.daily_rule.except_months(combination)
                self.assertEqual(self.daily_rule.spec['exceptMonths'], combination)

        self.assertEqual(combination_count, 4094)

        # Lets try some invalids
        self.assertRaises(voluptuous.MultipleInvalid, self.daily_rule.except_months, (0, ))
        self.assertRaises(voluptuous.MultipleInvalid, self.daily_rule.except_months, (13,))
        # We cannot allow all the months of the year to be excluded from the rule
        self.assertRaises(voluptuous.MultipleInvalid, self.daily_rule.except_months, turoboro.MONTHS)

    def test_hour(self):
        for hour in range(0, 24):
            self.daily_rule.hour(hour)
            self.assertEqual(self.daily_rule.spec['hour'], hour)

        self.assertRaises(voluptuous.MultipleInvalid, self.daily_rule.hour, -1)
        self.assertRaises(voluptuous.MultipleInvalid, self.daily_rule.hour, 24)

    def test_end(self):
        # End date cannot be before start date
        self.assertRaises(ValueError, self.daily_rule.end, turoboro.common.datetime_from_isoformat('2013-12-31T00:00:00'))
        self.daily_rule.end(turoboro.common.datetime_from_isoformat('2014-05-30T00:00:00'))
        self.assertEqual(self.daily_rule.spec['end'], '2014-05-30T00:00:00')


class DailyRuleComputeTests(unittest.TestCase):
    def setUp(self):
        self.starting_point = turoboro.common.datetime_from_isoformat('2014-01-01T00:00:00')
        self.daily_rule = turoboro.rules.DailyRule(self.starting_point)

    def test_basic(self):
        expected = '2014-01-02T00:00:00'
        actual = self.daily_rule.compute()

        self.assertEqual(expected, actual)

    def test_manipulate_hour(self):
        expected = '2014-01-02T03:00:00'
        self.daily_rule.hour(3)
        actual = self.daily_rule.compute()

        self.assertEqual(expected, actual)

    def test_count(self):
        expected = ['2014-01-02T00:00:00', '2014-01-03T00:00:00', '2014-01-04T00:00:00']
        actual = self.daily_rule.compute(count=3)
        self.assertEqual(expected, actual)

    def test_manipulate_repeat_over_weekends(self):
        """
        We're asking for every third day, for the next coming 8 iterations, except on weekends. Starting on
        January 1st 2014 that would exclude the 4th and the 19th from the list.
        """
        expected = ['2014-01-07T00:00:00', '2014-01-10T00:00:00', '2014-01-13T00:00:00', '2014-01-16T00:00:00',
                    '2014-01-22T00:00:00']
        self.daily_rule.repeat(3)
        self.daily_rule.except_days(turoboro.WEEKEND)
        actual = self.daily_rule.compute(count=7)
        self.assertEqual(expected, actual)

    def test_manipulate_repeat_over_months(self):
        """
        We're asking for every third day, for the next coming 21 iterations, except in February. Starting on
        January 1st 2014 that would exclude any days in February
        """
        expected = [
            '2014-01-04T00:00:00', '2014-01-07T00:00:00', '2014-01-10T00:00:00', '2014-01-13T00:00:00',
            '2014-01-16T00:00:00', '2014-01-19T00:00:00', '2014-01-22T00:00:00', '2014-01-25T00:00:00',
            '2014-01-28T00:00:00', '2014-01-31T00:00:00', '2014-03-02T00:00:00', '2014-03-05T00:00:00'
        ]
        self.daily_rule.repeat(3)
        self.daily_rule.except_months((turoboro.FEBRUARY,))
        actual = self.daily_rule.compute(count=21)
        self.assertEqual(expected, actual)

    def test_manipulate_end(self):
        self.daily_rule.end(turoboro.common.datetime_from_isoformat('2014-05-30T00:00:00'))
        self.daily_rule.repeat(7)
        expected = ['2014-01-08T00:00:00', '2014-01-15T00:00:00', '2014-01-22T00:00:00', '2014-01-29T00:00:00',
                    '2014-02-05T00:00:00', '2014-02-12T00:00:00', '2014-02-19T00:00:00', '2014-02-26T00:00:00',
                    '2014-03-05T00:00:00', '2014-03-12T00:00:00', '2014-03-19T00:00:00', '2014-03-26T00:00:00',
                    '2014-04-02T00:00:00', '2014-04-09T00:00:00', '2014-04-16T00:00:00', '2014-04-23T00:00:00',
                    '2014-04-30T00:00:00', '2014-05-07T00:00:00', '2014-05-14T00:00:00', '2014-05-21T00:00:00',
                    '2014-05-28T00:00:00']
        actual = self.daily_rule.compute(count=turoboro.FULL_RANGE)
        self.assertEqual(expected, actual)

    def test_staggered_once(self):
        self.daily_rule.repeat(7).end(turoboro.common.datetime_from_isoformat('2014-05-30T00:00:00'))
        expected = '2014-03-12T00:00:00'
        actual = self.daily_rule.compute(
            starting_at=turoboro.common.datetime_from_isoformat('2014-03-08T00:00:00')
        )
        self.assertEqual(expected, actual)

    def test_staggered_in_chain(self):
        self.daily_rule.repeat(7).end(turoboro.common.datetime_from_isoformat('2014-05-30T00:00:00'))
        expected = ['2014-03-12T00:00:00', '2014-03-19T00:00:00', '2014-03-26T00:00:00',
                    '2014-04-02T00:00:00']
        actual = self.daily_rule.compute(
            starting_at=turoboro.common.datetime_from_isoformat('2014-03-08T00:00:00'),
            count=4
        )
        self.assertEqual(expected, actual)
