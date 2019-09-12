import unittest
from datetime import datetime
import turoboro.weekly_rule
import turoboro.constants
import voluptuous
import itertools
import turoboro.common


class WeeklyRuleSetupTests(unittest.TestCase):
    def setUp(self):
        self.starting_point = datetime(2014, 1, 1)
        self.weekly_rule = turoboro.WeeklyRule(
            self.starting_point, (turoboro.MONDAY, turoboro.THURSDAY), timezone='America/Chicago'
        )

    def test_default_spec(self):
        expected = {
            'on_days': (turoboro.MONDAY, turoboro.THURSDAY),
            'except_months': None,
            'on_hour': 0,
            'every_nth_week': 1,
            'rule': 'weekly',
            'repeat': None,
            'start': '2014-01-01T00:00:00-06:00',
            'end': None,
            'timezone': 'America/Chicago'
        }

        self.assertEqual(self.weekly_rule.spec, expected)

    def test_every_nth_week(self):
        self.assertRaises(voluptuous.MultipleInvalid, self.weekly_rule.every_nth_week, 0)
        self.assertRaises(voluptuous.MultipleInvalid, self.weekly_rule.every_nth_week, 54)
        for every_nth in range(1, 53):
            self.weekly_rule.every_nth_week(every_nth)
            self.assertEqual(self.weekly_rule.spec['every_nth_week'], every_nth)
        self.assertEqual(self.weekly_rule, self.weekly_rule.every_nth_week(10))

    def test_on_days(self):
        """
        There are 127 valid ways in which to specify days of the week on which to do something.
        """
        # Set up all combinations of days of weeks that are at least ONE day and at the most SEVEN.
        valid_combination_sets = [list(itertools.combinations(turoboro.DAYS, n)) for n in range(1, 8)]
        combination_count = 0
        for valid_combinations_in_range in valid_combination_sets:
            for combination in valid_combinations_in_range:
                combination_count += 1
                self.weekly_rule.on_days(*combination)
                self.assertEqual(self.weekly_rule.spec['on_days'], combination)

        self.assertEqual(combination_count, 127)

        # Lets try some invalids
        self.assertRaises(voluptuous.MultipleInvalid, self.weekly_rule.on_days, -1)
        self.assertRaises(voluptuous.MultipleInvalid, self.weekly_rule.on_days, 7)
        # We cannot allow all the days of the week to be excluded from the rule
        self.assertRaises(ValueError, self.weekly_rule.on_days, None)


class WeeklyRuleWithEndDateTests(unittest.TestCase):
    def test_kathmandu(self):
        weekly_rule = turoboro.WeeklyRule(datetime(2014, 1, 1), on_days=turoboro.WEEKEND, timezone='Asia/Kathmandu',
                                          every_nth_week=4)
        weekly_rule.end_on(datetime(2014, 1, 31))
        weekly_rule.on_hour(8)
        result = weekly_rule.compute()
        self.assertEqual(result.count, 2)
        self.assertEqual(result.first, '2014-01-04T02:15:00+00:00')

    def test(self):
        weekly_rule = turoboro.WeeklyRule(datetime(2014, 1, 1), on_days=turoboro.WEEKEND)
        # 1. Lets try a weekly rule that repeats on both Sat and Sun until the 31st
        weekly_rule.end_on(datetime(2014, 1, 31))
        result = weekly_rule.compute()

        # 2. There are 8 days that are on a weekend between 2014-01-01 and 2014-01-31
        self.assertEqual(result.count, 8)
        self.assertEqual(result.first, '2014-01-04T00:00:00+00:00')

        # 3. Lets set a specific hour and make sure it pans out
        weekly_rule.on_hour(8)
        result = weekly_rule.compute()
        self.assertEqual(result.first, '2014-01-04T08:00:00+00:00')
        self.assertEqual(result.last, '2014-01-26T08:00:00+00:00')
        expected_all = ['2014-01-04T08:00:00+00:00', '2014-01-05T08:00:00+00:00', '2014-01-11T08:00:00+00:00',
                        '2014-01-12T08:00:00+00:00', '2014-01-18T08:00:00+00:00', '2014-01-19T08:00:00+00:00',
                        '2014-01-25T08:00:00+00:00', '2014-01-26T08:00:00+00:00']
        self.assertEqual(result.all, expected_all)

        # 4. Lets try with timestamps instead
        expected_all_posix = [
            turoboro.common.convert_datetime_to(datetime.strptime(iso, '%Y-%m-%dT%H:%M:%S+00:00'), turoboro.POSIX)
            for iso in expected_all
        ]
        result = weekly_rule.compute(return_as=turoboro.POSIX)
        self.assertEqual(result.all, expected_all_posix)

        # 5. Lets change to every third week, until March 31th 2014, excepting February
        weekly_rule.every_nth_week(3).except_months(turoboro.FEBRUARY).end_on(datetime(2014, 3, 31))
        expected_all = ['2014-01-04T08:00:00+00:00', '2014-01-05T08:00:00+00:00',
                        '2014-01-25T08:00:00+00:00', '2014-01-26T08:00:00+00:00',
                        '2014-03-08T08:00:00+00:00', '2014-03-09T08:00:00+00:00',
                        '2014-03-29T08:00:00+00:00', '2014-03-30T08:00:00+00:00']
        result = weekly_rule.compute()
        self.assertEqual(result.all, expected_all)

        # 6. Lets get a segment out of our result
        expected_segment = ['2014-03-08T08:00:00+00:00', '2014-03-09T08:00:00+00:00',
                            '2014-03-29T08:00:00+00:00', '2014-03-30T08:00:00+00:00']
        self.assertEqual(result.segment(datetime(2014, 1, 31)), expected_segment)
        self.assertEqual(result.segment(datetime(2014, 3, 31)), [])
        expected_segment = ['2014-01-25T08:00:00+00:00', '2014-01-26T08:00:00+00:00',
                            '2014-03-08T08:00:00+00:00', '2014-03-09T08:00:00+00:00']
        self.assertEqual(result.segment(datetime(2014, 1, 20), datetime(2014, 3, 12)), expected_segment)

    def test_staggered(self):
        weekly_rule = turoboro.WeeklyRule(
            datetime(2014, 1, 1), on_days=(turoboro.WEDNESDAY,), end_on=datetime(2014, 12, 31), every_nth_week=7,
            except_months=(turoboro.FEBRUARY, turoboro.OCTOBER), on_hour=14)

        result = weekly_rule.compute()
        expected_all = ['2014-01-01T14:00:00+00:00', '2014-04-09T14:00:00+00:00', '2014-05-28T14:00:00+00:00',
                        '2014-07-16T14:00:00+00:00', '2014-09-03T14:00:00+00:00', '2014-12-10T14:00:00+00:00']
        self.assertEqual(expected_all, result.all)
        result_staggered = weekly_rule.compute(from_dt=datetime(2014, 5, 29))
        self.assertEqual(result_staggered.first, '2014-07-16T14:00:00+00:00')
        self.assertEqual(result_staggered.last, '2014-12-10T14:00:00+00:00')
        self.assertEqual(result_staggered.count, 3)
        result_staggered = weekly_rule.compute(from_dt=datetime(2014, 11, 23))
        self.assertEqual(result_staggered.first, '2014-12-10T14:00:00+00:00')
        self.assertEqual(result_staggered.last, '2014-12-10T14:00:00+00:00')
        self.assertEqual(result_staggered.count, 1)


class WeeklyRuleWithRepeatNTimesTests(unittest.TestCase):
    def test(self):
        weekly_rule = turoboro.WeeklyRule(
            datetime(2014, 1, 1), repeat_n_times=10, on_days=(turoboro.THURSDAY, turoboro.SUNDAY),
            on_hour=8, every_nth_week=2
        )
        expected = ['2014-01-02T08:00:00+00:00', '2014-01-05T08:00:00+00:00', '2014-01-16T08:00:00+00:00',
                    '2014-01-19T08:00:00+00:00', '2014-01-30T08:00:00+00:00', '2014-02-02T08:00:00+00:00',
                    '2014-02-13T08:00:00+00:00', '2014-02-16T08:00:00+00:00', '2014-02-27T08:00:00+00:00',
                    '2014-03-02T08:00:00+00:00']

        result = weekly_rule.compute()
        self.assertEqual(result.count, 10)
        self.assertEqual(result.first, '2014-01-02T08:00:00+00:00')
        self.assertEqual(result.last, '2014-03-02T08:00:00+00:00')
        self.assertEqual(expected, result.all)

        # Lets change to every third week, excepting February, and 15 counts
        weekly_rule.every_nth_week(3).except_months(turoboro.FEBRUARY).repeat_n_times(15)
        expected_all = ['2014-01-02T08:00:00+00:00', '2014-01-05T08:00:00+00:00', '2014-01-23T08:00:00+00:00',
                        '2014-01-26T08:00:00+00:00', '2014-03-06T08:00:00+00:00', '2014-03-09T08:00:00+00:00',
                        '2014-03-27T08:00:00+00:00', '2014-03-30T08:00:00+00:00', '2014-04-17T08:00:00+00:00',
                        '2014-04-20T08:00:00+00:00', '2014-05-08T08:00:00+00:00', '2014-05-11T08:00:00+00:00',
                        '2014-05-29T08:00:00+00:00', '2014-06-01T08:00:00+00:00', '2014-06-19T08:00:00+00:00']

        result = weekly_rule.compute()
        self.assertEqual(expected_all, result.all)

        # Lets get a segment out of our result
        expected_segment = ['2014-03-06T08:00:00+00:00', '2014-03-09T08:00:00+00:00', '2014-03-27T08:00:00+00:00',
                            '2014-03-30T08:00:00+00:00', '2014-04-17T08:00:00+00:00', '2014-04-20T08:00:00+00:00',
                            '2014-05-08T08:00:00+00:00', '2014-05-11T08:00:00+00:00', '2014-05-29T08:00:00+00:00',
                            '2014-06-01T08:00:00+00:00', '2014-06-19T08:00:00+00:00']
        self.assertEqual(result.segment(datetime(2014, 1, 31)), expected_segment)
        self.assertEqual(result.segment(datetime(2014, 6, 20)), [])
        expected_segment = ['2014-01-23T08:00:00+00:00', '2014-01-26T08:00:00+00:00', '2014-03-06T08:00:00+00:00',
                            '2014-03-09T08:00:00+00:00']
        self.assertEqual(result.segment(datetime(2014, 1, 20), datetime(2014, 3, 12)), expected_segment)

    def test_staggered(self):
        weekly_rule = turoboro.WeeklyRule(
            datetime(2014, 1, 1), repeat_n_times=44, every_nth_week=8, on_days=(turoboro.THURSDAY, turoboro.SUNDAY),
            except_months=(turoboro.FEBRUARY, turoboro.OCTOBER), on_hour=14)

        expected_all = ['2014-01-02T14:00:00+00:00', '2014-01-05T14:00:00+00:00', '2014-03-02T14:00:00+00:00',
                        '2014-04-24T14:00:00+00:00', '2014-04-27T14:00:00+00:00', '2014-06-19T14:00:00+00:00',
                        '2014-06-22T14:00:00+00:00', '2014-08-14T14:00:00+00:00', '2014-08-17T14:00:00+00:00',
                        '2014-12-04T14:00:00+00:00', '2014-12-07T14:00:00+00:00', '2015-01-29T14:00:00+00:00',
                        '2015-03-26T14:00:00+00:00', '2015-03-29T14:00:00+00:00', '2015-05-21T14:00:00+00:00',
                        '2015-05-24T14:00:00+00:00', '2015-07-16T14:00:00+00:00', '2015-07-19T14:00:00+00:00',
                        '2015-09-10T14:00:00+00:00', '2015-09-13T14:00:00+00:00', '2015-11-05T14:00:00+00:00',
                        '2015-11-08T14:00:00+00:00', '2015-12-31T14:00:00+00:00', '2016-01-03T14:00:00+00:00',
                        '2016-04-21T14:00:00+00:00', '2016-04-24T14:00:00+00:00', '2016-06-16T14:00:00+00:00',
                        '2016-06-19T14:00:00+00:00', '2016-08-11T14:00:00+00:00', '2016-08-14T14:00:00+00:00',
                        '2016-12-01T14:00:00+00:00', '2016-12-04T14:00:00+00:00', '2017-01-26T14:00:00+00:00',
                        '2017-01-29T14:00:00+00:00', '2017-03-23T14:00:00+00:00', '2017-03-26T14:00:00+00:00',
                        '2017-05-18T14:00:00+00:00', '2017-05-21T14:00:00+00:00', '2017-07-13T14:00:00+00:00',
                        '2017-07-16T14:00:00+00:00', '2017-09-07T14:00:00+00:00', '2017-09-10T14:00:00+00:00',
                        '2017-11-02T14:00:00+00:00', '2017-11-05T14:00:00+00:00']

        result = weekly_rule.compute()
        self.assertEqual(expected_all, result.all)
        result_staggered = weekly_rule.compute(from_dt=datetime(2015, 12, 1))
        self.assertEqual(result_staggered.count, 22)
        self.assertEqual(result_staggered.first, '2015-12-31T14:00:00+00:00')
        self.assertEqual(result_staggered.last, '2017-11-05T14:00:00+00:00')
        result_staggered = weekly_rule.compute(from_dt=datetime(2017, 9, 8))
        self.assertEqual(result_staggered.first, '2017-09-10T14:00:00+00:00')
        self.assertEqual(result_staggered.last, '2017-11-05T14:00:00+00:00')
        self.assertEqual(result_staggered.count, 3)

    def test_next(self):
        weekly_rule = turoboro.WeeklyRule(
            datetime(2014, 1, 1), repeat_n_times=44, every_nth_week=8, on_days=(turoboro.THURSDAY, turoboro.SUNDAY),
            except_months=(turoboro.FEBRUARY, turoboro.OCTOBER), on_hour=14
        )
        result = weekly_rule.result()
        self.assertEqual(next(result), '2014-01-02T14:00:00+00:00')
        self.assertEqual(next(result), '2014-01-05T14:00:00+00:00')

    def test_next_kathmandu(self):
        """ Kathmandu is +5.45h so, 14 hours in Kathmandu is 8.15 in UTC """
        weekly_rule = turoboro.WeeklyRule(
            datetime(2014, 1, 1), repeat_n_times=44, every_nth_week=8, on_days=(turoboro.THURSDAY, turoboro.SUNDAY),
            except_months=(turoboro.FEBRUARY, turoboro.OCTOBER), on_hour=14, timezone='Asia/Kathmandu'
        )
        result = weekly_rule.result()
        self.assertEqual(next(result), '2014-01-02T08:15:00+00:00')
        self.assertEqual(next(result), '2014-01-05T08:15:00+00:00')


class WeeklyInfiniteRuleTests(unittest.TestCase):
    def test(self):
        expected_100 = ['2014-01-04T08:00:00+00:00', '2014-01-05T08:00:00+00:00', '2014-02-08T08:00:00+00:00',
                        '2014-02-09T08:00:00+00:00', '2014-03-15T08:00:00+00:00', '2014-03-16T08:00:00+00:00',
                        '2014-04-19T08:00:00+00:00', '2014-04-20T08:00:00+00:00', '2014-05-24T08:00:00+00:00',
                        '2014-05-25T08:00:00+00:00', '2014-06-28T08:00:00+00:00', '2014-06-29T08:00:00+00:00',
                        '2014-08-02T08:00:00+00:00', '2014-08-03T08:00:00+00:00', '2014-09-06T08:00:00+00:00',
                        '2014-09-07T08:00:00+00:00', '2014-10-11T08:00:00+00:00', '2014-10-12T08:00:00+00:00',
                        '2014-11-15T08:00:00+00:00', '2014-11-16T08:00:00+00:00', '2014-12-20T08:00:00+00:00',
                        '2014-12-21T08:00:00+00:00', '2015-01-24T08:00:00+00:00', '2015-01-25T08:00:00+00:00',
                        '2015-02-28T08:00:00+00:00', '2015-03-01T08:00:00+00:00', '2015-04-04T08:00:00+00:00',
                        '2015-04-05T08:00:00+00:00', '2015-05-09T08:00:00+00:00', '2015-05-10T08:00:00+00:00',
                        '2015-06-13T08:00:00+00:00', '2015-06-14T08:00:00+00:00', '2015-07-18T08:00:00+00:00',
                        '2015-07-19T08:00:00+00:00', '2015-08-22T08:00:00+00:00', '2015-08-23T08:00:00+00:00',
                        '2015-09-26T08:00:00+00:00', '2015-09-27T08:00:00+00:00', '2015-10-31T08:00:00+00:00',
                        '2015-11-01T08:00:00+00:00', '2015-12-05T08:00:00+00:00', '2015-12-06T08:00:00+00:00',
                        '2016-01-09T08:00:00+00:00', '2016-01-10T08:00:00+00:00', '2016-02-13T08:00:00+00:00',
                        '2016-02-14T08:00:00+00:00', '2016-03-19T08:00:00+00:00', '2016-03-20T08:00:00+00:00',
                        '2016-04-23T08:00:00+00:00', '2016-04-24T08:00:00+00:00', '2016-05-28T08:00:00+00:00',
                        '2016-05-29T08:00:00+00:00', '2016-07-02T08:00:00+00:00', '2016-07-03T08:00:00+00:00',
                        '2016-08-06T08:00:00+00:00', '2016-08-07T08:00:00+00:00', '2016-09-10T08:00:00+00:00',
                        '2016-09-11T08:00:00+00:00', '2016-10-15T08:00:00+00:00', '2016-10-16T08:00:00+00:00',
                        '2016-11-19T08:00:00+00:00', '2016-11-20T08:00:00+00:00', '2016-12-24T08:00:00+00:00',
                        '2016-12-25T08:00:00+00:00', '2017-01-28T08:00:00+00:00', '2017-01-29T08:00:00+00:00',
                        '2017-03-04T08:00:00+00:00', '2017-03-05T08:00:00+00:00', '2017-04-08T08:00:00+00:00',
                        '2017-04-09T08:00:00+00:00', '2017-05-13T08:00:00+00:00', '2017-05-14T08:00:00+00:00',
                        '2017-06-17T08:00:00+00:00', '2017-06-18T08:00:00+00:00', '2017-07-22T08:00:00+00:00',
                        '2017-07-23T08:00:00+00:00', '2017-08-26T08:00:00+00:00', '2017-08-27T08:00:00+00:00',
                        '2017-09-30T08:00:00+00:00', '2017-10-01T08:00:00+00:00', '2017-11-04T08:00:00+00:00',
                        '2017-11-05T08:00:00+00:00', '2017-12-09T08:00:00+00:00', '2017-12-10T08:00:00+00:00',
                        '2018-01-13T08:00:00+00:00', '2018-01-14T08:00:00+00:00', '2018-02-17T08:00:00+00:00',
                        '2018-02-18T08:00:00+00:00', '2018-03-24T08:00:00+00:00', '2018-03-25T08:00:00+00:00',
                        '2018-04-28T08:00:00+00:00', '2018-04-29T08:00:00+00:00', '2018-06-02T08:00:00+00:00',
                        '2018-06-03T08:00:00+00:00', '2018-07-07T08:00:00+00:00', '2018-07-08T08:00:00+00:00',
                        '2018-08-11T08:00:00+00:00', '2018-08-12T08:00:00+00:00', '2018-09-15T08:00:00+00:00',
                        '2018-09-16T08:00:00+00:00']

        expected_20 = ['2015-12-05T08:00:00+00:00', '2015-12-06T08:00:00+00:00',
                       '2016-01-09T08:00:00+00:00', '2016-01-10T08:00:00+00:00', '2016-02-13T08:00:00+00:00',
                       '2016-02-14T08:00:00+00:00', '2016-03-19T08:00:00+00:00', '2016-03-20T08:00:00+00:00',
                       '2016-04-23T08:00:00+00:00', '2016-04-24T08:00:00+00:00', '2016-05-28T08:00:00+00:00',
                       '2016-05-29T08:00:00+00:00', '2016-07-02T08:00:00+00:00', '2016-07-03T08:00:00+00:00',
                       '2016-08-06T08:00:00+00:00', '2016-08-07T08:00:00+00:00', '2016-09-10T08:00:00+00:00',
                       '2016-09-11T08:00:00+00:00', '2016-10-15T08:00:00+00:00', '2016-10-16T08:00:00+00:00']

        weekly_rule = turoboro.WeeklyRule(datetime(2014, 1, 1), every_nth_week=5, on_days=turoboro.WEEKEND, on_hour=8)
        weekly_rule2 = turoboro.WeeklyRule(datetime(2014, 1, 1), every_nth_week=5, on_days=turoboro.WEEKEND, on_hour=8,
                                           end_on=datetime(2018, 9, 19))
        result = weekly_rule.compute()
        result2 = weekly_rule2.compute()
        self.assertTrue(result.infinite)
        self.assertEqual(result.count, 100)
        self.assertEqual(result2.count, 100)
        self.assertEqual(result.first, result2.first)
        self.assertEqual(result2.all, expected_100)
        self.assertEqual(result.first, '2014-01-04T08:00:00+00:00')
        self.assertEqual(result.last, '2018-09-16T08:00:00+00:00')

        result = weekly_rule.compute(datetime(2015, 11, 27), max_count_if_infinite=20)
        weekly_rule2 = turoboro.WeeklyRule(datetime(2014, 1, 1), end_on=datetime(2018, 11, 19), every_nth_week=5,
                                           on_days=turoboro.WEEKEND, on_hour=8)
        result2 = weekly_rule2.compute(datetime(2015, 11, 27))
        self.assertTrue(result.infinite)
        self.assertEqual(result.count, 20)
        self.assertEqual(result.first, result2.first)
        self.assertEqual(result2.all[:20], expected_20)
        self.assertEqual(result.first, '2015-12-05T08:00:00+00:00')
        self.assertEqual(result.last, '2016-10-16T08:00:00+00:00')

    def test_next(self):
        daily_rule = turoboro.DailyRule(
            datetime(2014, 1, 1), every_nth_day=7, except_weekdays=turoboro.WEEKEND,
            except_months=(turoboro.FEBRUARY, turoboro.OCTOBER), on_hour=14
        )

        result = daily_rule.result(datetime.utcnow())
        for res in result:
            daily_rule._is_allowed(turoboro.common.datetime_from_isoformat(res))
