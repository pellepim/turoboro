import unittest
import turoboro
import voluptuous


class FromSpecTests(unittest.TestCase):
    def test_daily_from_spec(self):
        json_spec = """
            {
                "end": "2014-02-01T00:00:00+00:00",
                "every_nth_day": 2,
                "except_days": [5, 6],
                "except_months": null,
                "on_hour": 8,
                "repeat": null,
                "rule": "daily",
                "start": "2014-01-01T08:00:00+00:00",
                "timezone": "UTC"
            }
        """
        daily_rule = turoboro.Rule.from_spec(json_spec)
        self.assertTrue(isinstance(daily_rule, turoboro.DailyRule))

    def test_daily_from_invalid_spec(self):
        json_spec = """
            {
                "end": "2014-02-01T00:00:00+00:00",
                "every_nth_day": 2,
                "except_days": [5, 6, 10],
                "except_months": null,
                "on_hour": 8,
                "repeat": null,
                "rule": "daily",
                "start": "2014-01-01T08:00:00+00:00",
                "timezone": "UTC"
            }
        """
        self.assertRaises(voluptuous.MultipleInvalid, turoboro.Rule.from_spec, json_spec)
        
    def test_weekly_from_spec(self):
        json_spec = """{
            "end": "2015-01-12T00:00:00+00:00",
            "every_nth_week": 4,
            "except_months": null,
            "on_days": [5, 6],
            "on_hour": 0,
            "repeat": null,
            "rule": "weekly",
            "start": "2014-01-01T00:00:00+00:00",
            "timezone": "UTC"
        }"""
        weekly_rule = turoboro.Rule.from_spec(json_spec)
        self.assertTrue(isinstance(weekly_rule, turoboro.WeeklyRule))

    def test_weekly_from_invalid_spec(self):
        json_spec = """{
            "end": "2015-01-12T00:00:00+00:00",
            "every_nth_week": 4,
            "except_months": null,
            "on_days": [],
            "on_hour": 0,
            "repeat": null,
            "rule": "weekly",
            "start": "2014-01-01T00:00:00+00:00",
            "timezone": "UTC"
        }"""
        self.assertRaises(voluptuous.MultipleInvalid, turoboro.Rule.from_spec, json_spec)
