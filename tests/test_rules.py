import unittest
import turoboro.rules
from datetime import datetime
import voluptuous
import itertools


class DailyRuleTests(unittest.TestCase):
    def setUp(self):
        self.starting_point = datetime.strptime('2014-01-01T00:00:00', '%Y-%m-%dT%H:%M:%S')
        self.daily_rule = turoboro.rules.DailyRule(self.starting_point)

    def test_default_spec(self):
        expected = {
            'exceptDays': None,
            'exceptMonths': None,
            'hour': 0,
            'repeat': 1,
            'rule': 'daily',
            'start': '2014-01-01T00:00:00'
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

    