import unittest
from datetime import datetime
import turoboro


class WeeklyRuleSetupTests(unittest.TestCase):
    def setUp(self):
        self.starting_point = datetime(2014, 1, 1)
        self.day_of_month_rule = turoboro.MonthlyRule(
            self.starting_point, day_of_month=28, every_nth_month=2, end_on=datetime(2015, 2, 1)
        )
        self.weekday_month_rule = turoboro.MonthlyRule(
            self.starting_point, every_nth_month=3, end_on=datetime(2015, 1, 2), weekday_count=3,
            weekday=turoboro.THURSDAY, except_months=(turoboro.JULY, turoboro.AUGUST), on_hour=4,
            timezone='America/Chicago'
        )

    def test_default_spec(self):
        expect_day_of_month_rule = {
            'start': '2014-01-01T00:00:00+00:00',
            'end': '2015-02-02T00:00:00+00:00',
            'repeat': None,
            'rule': 'monthly',
            'day_of_month_rule': {
                'day': 28,
                'every_nth': 2
            },
            'weekday_rule': None,
            'except_months': None,
            'on_hour': 0,
            'timezone': 'UTC'
        }

        self.assertEqual(self.day_of_month_rule.spec, expect_day_of_month_rule)

        expect_week_month_rule = {
            'start': '2014-01-01T04:00:00-06:00',
            'end': '2015-01-03T04:00:00-06:00',
            'repeat': None,
            'rule': 'monthly',
            'day_of_month_rule': None,
            'weekday_rule': {
                'count': 3,
                'weekday': turoboro.THURSDAY,
                'every_nth': 3
            },
            'except_months': (turoboro.JULY, turoboro.AUGUST),
            'on_hour': 4,
            'timezone': 'America/Chicago'
        }

        self.assertEqual(self.weekday_month_rule.spec, expect_week_month_rule)

    def test_day_of_month_rule(self):
        self.weekday_month_rule.day_of_month(5, 5)
        self.assertIsNone(self.weekday_month_rule.spec['weekday_rule'])
        self.assertEqual(self.weekday_month_rule.spec['day_of_month_rule'], {
            'day': 5,
            'every_nth': 5
        })

    def test_weekday_rule(self):
        self.day_of_month_rule.weekday(5, turoboro.THURSDAY, 2)
        self.assertIsNone(self.day_of_month_rule.spec['day_of_month_rule'])
        self.assertEqual(self.day_of_month_rule.spec['weekday_rule'], {
            'count': 5,
            'weekday': turoboro.THURSDAY,
            'every_nth': 2
        })


class MonthlyRuleWithEndDatesTests(unittest.TestCase):
    def _test_day_of_month(self):
        day_of_month_rule = turoboro.MonthlyRule(datetime(2014, 1, 1), day_of_month=31, end_on=datetime(2014, 12, 31))

        result = day_of_month_rule.compute()
        