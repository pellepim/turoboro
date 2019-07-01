import unittest
from datetime import datetime
import turoboro
import turoboro.common
import voluptuous
import itertools


class DailyRuleSetupTests(unittest.TestCase):
    def setUp(self):
        self.starting_point = datetime(2014, 1, 1)
        self.daily_rule = turoboro.DailyRule(self.starting_point)

    def test_default_spec(self):
        expected = {
            'except_days': None,
            'except_months': None,
            'on_hour': 0,
            'every_nth_day': 1,
            'rule': 'daily',
            'repeat': None,
            'start': '2014-01-01T00:00:00+00:00',
            'end': None,
            'timezone': 'UTC'
        }

        self.assertEqual(self.daily_rule.spec, expected)

    def test_every_nth_day(self):
        """ Every nth may be between 1 and 365"""
        self.assertRaises(voluptuous.MultipleInvalid, self.daily_rule.every_nth_day, 0)
        self.assertRaises(voluptuous.MultipleInvalid, self.daily_rule.every_nth_day, 366)
        for every_nth in range(2, 8):
            self.daily_rule.every_nth_day(every_nth)
            self.assertEqual(self.daily_rule.spec['every_nth_day'], every_nth)
        self.assertEqual(self.daily_rule, self.daily_rule.every_nth_day(1))

    def test_except_weekdays(self):
        """
        There are 126 valid ways in which to specify days of the week on which to NOT do something. We cannot
        allow to except all 7 days from the rule - because then what would be the use of the rule?

        Also, whenever we except the starting day - we should raise an exception.
        """
        # Set up all combinations of days of weeks that are at least ONE day and at the most SIX.
        valid_combination_sets = [list(itertools.combinations(turoboro.DAYS, n)) for n in range(1, 7)]
        combination_count = 0
        for valid_combinations_in_range in valid_combination_sets:
            for combination in valid_combinations_in_range:
                combination_count += 1

                # If we try to set an exception which include the starting date - we should raise an exception
                if self.starting_point.weekday() in combination:
                    self.assertRaises(ValueError, self.daily_rule.except_weekdays, *combination)
                # Otherwise we simply accept the order and store it on the spec
                else:
                    self.daily_rule.except_weekdays(*combination)
                    self.assertEqual(self.daily_rule.spec['except_days'], combination)

        self.assertEqual(combination_count, 126)

        # Lets try some invalids
        self.assertRaises(voluptuous.MultipleInvalid, self.daily_rule.except_weekdays, -1)
        self.assertRaises(voluptuous.MultipleInvalid, self.daily_rule.except_weekdays, 7)
        # We cannot allow all the days of the week to be excluded from the rule
        self.assertRaises(ValueError, self.daily_rule.except_weekdays, *turoboro.DAYS)

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
                # If we try to set an exception which includes the month of the start date - we should raise
                # an exception
                if self.starting_point.month in combination:
                    self.assertRaises(ValueError, self.daily_rule.except_months, *combination)
                # Otherwise we accept the order and store it on the spec
                else:
                    self.daily_rule.except_months(*combination)
                    self.assertEqual(self.daily_rule.spec['except_months'], combination)

        self.assertEqual(combination_count, 4094)

        # Lets try some invalids
        self.assertRaises(voluptuous.MultipleInvalid, self.daily_rule.except_months, (0,))
        self.assertRaises(voluptuous.MultipleInvalid, self.daily_rule.except_months, (13,))
        # We cannot allow all the months of the year to be excluded from the rule
        self.assertRaises(ValueError, self.daily_rule.except_months, *turoboro.MONTHS)

    def test_hour(self):
        for hour in range(0, 24):
            self.daily_rule.on_hour(hour)
            self.assertEqual(self.daily_rule.spec['on_hour'], hour)

        self.assertRaises(voluptuous.MultipleInvalid, self.daily_rule.on_hour, -1)
        self.assertRaises(voluptuous.MultipleInvalid, self.daily_rule.on_hour, 24)

    def test_end_before(self):
        # End date cannot be before start date, and a repeat n times-rule may not be set after an end date
        # has been specified
        self.assertRaises(ValueError, self.daily_rule._end_before,
                          turoboro.common.datetime_from_isoformat('2013-12-31T00:00:00'))
        self.daily_rule._end_before(turoboro.common.datetime_from_isoformat('2014-05-30T00:00:00'))
        self.assertEqual(self.daily_rule.spec['end'], '2014-05-30T00:00:00')
        self.assertRaises(ValueError, self.daily_rule.repeat_n_times, 10)

    def test_end_on(self):
        self.daily_rule.end_on(turoboro.common.datetime_from_isoformat('2014-05-30T00:00:00'))
        self.assertEqual(self.daily_rule.spec['end'], '2014-05-31T00:00:00+00:00')

    def test_repeat_n_times(self):
        self.daily_rule.repeat_n_times(10)
        self.assertEqual(self.daily_rule.spec['repeat'], 10)
        self.assertRaises(ValueError, self.daily_rule._end_before,
                          turoboro.common.datetime_from_isoformat('2014-12-31T00:00:00'))

    def test_raises(self):
        # The starting date is a Wednesday - we may not exclude wednesdays as valid...
        self.assertRaises(ValueError, self.daily_rule.except_weekdays, turoboro.WEDNESDAY)
        # The starting date is in January - we may not exclude January as valid..
        self.assertRaises(ValueError, self.daily_rule.except_months, turoboro.JANUARY)
        # We cannot pick an earlier end date than the start date
        self.assertRaises(ValueError, self.daily_rule.end_on, datetime(2013, 12, 31))
        # We're not allowed to set a repeat count if we have an end date
        self.daily_rule.end_on(datetime(2014, 1, 31))
        self.assertRaises(ValueError, self.daily_rule.repeat_n_times, 10)
        # We're not allowed to set an end date if we have a repeat count
        self.daily_rule.end_on(None)
        self.daily_rule.repeat_n_times(10)
        self.assertRaises(ValueError, self.daily_rule.end_on, datetime(2014, 1, 31))

    def test_invalid_start(self):
        self.assertRaises(ValueError, turoboro.DailyRule, 'asd')

    def test_reset_except_weekdays(self):
        daily_rule = turoboro.DailyRule(datetime(2014, 1, 1), except_weekdays=turoboro.WEEKEND)
        self.assertEqual(daily_rule.spec['except_days'], turoboro.WEEKEND)
        daily_rule.except_weekdays(None)
        self.assertEqual(daily_rule.spec['except_days'], None)

    def test_reset_except_months(self):
        daily_rule = turoboro.DailyRule(datetime(2014, 1, 1), except_months=(turoboro.FEBRUARY, turoboro.MARCH))
        self.assertEqual(daily_rule.spec['except_months'], (turoboro.FEBRUARY, turoboro.MARCH))
        daily_rule.except_months(None)
        self.assertEqual(daily_rule.spec['except_months'], None)

    def test_reset_end(self):
        daily_rule = turoboro.DailyRule(datetime(2014, 1, 1), datetime(2014, 5, 30))
        self.assertEqual(daily_rule.spec['end'], '2014-05-31T00:00:00+00:00')
        daily_rule.end_on(None)
        self.assertEqual(daily_rule.spec['end'], None)
        daily_rule = turoboro.DailyRule(datetime(2014, 1, 1), datetime(2014, 5, 30))
        daily_rule._end_before(None)
        self.assertEqual(daily_rule.spec['end'], None)

    def test_faulty_end_date(self):
        self.assertRaises(ValueError, turoboro.DailyRule, datetime(2014, 1, 1), datetime(2013, 12, 31))


class DailyRuleWithEndDateTests(unittest.TestCase):
    def test(self):
        daily_rule = turoboro.DailyRule(datetime(2014, 1, 1), except_weekdays=turoboro.WEEKEND)
        # 1. Lets try a daily rule that bypasses weekends for the duration of January 2014
        daily_rule.end_on(datetime(2014, 1, 31))
        result = daily_rule.compute()

        # 2. There are 23 days that do not fall on a weekend in January 2014
        self.assertEqual(result.count, 23)
        self.assertEqual(result.first, '2014-01-01T00:00:00')

        # 3. Lets set a specific hour and make sure it pans out
        daily_rule.on_hour(8)
        result = daily_rule.compute()
        self.assertEqual(result.first, '2014-01-01T08:00:00')
        self.assertEqual(result.last, '2014-01-31T08:00:00')
        expected_all = ['2014-01-01T08:00:00', '2014-01-02T08:00:00', '2014-01-03T08:00:00', '2014-01-06T08:00:00',
                        '2014-01-07T08:00:00', '2014-01-08T08:00:00', '2014-01-09T08:00:00', '2014-01-10T08:00:00',
                        '2014-01-13T08:00:00', '2014-01-14T08:00:00', '2014-01-15T08:00:00', '2014-01-16T08:00:00',
                        '2014-01-17T08:00:00', '2014-01-20T08:00:00', '2014-01-21T08:00:00', '2014-01-22T08:00:00',
                        '2014-01-23T08:00:00', '2014-01-24T08:00:00', '2014-01-27T08:00:00', '2014-01-28T08:00:00',
                        '2014-01-29T08:00:00', '2014-01-30T08:00:00', '2014-01-31T08:00:00']
        self.assertEqual(result.all, expected_all)

        # 4. Lets try with timestamps instead
        expected_all_posix = [1388563200, 1388649600, 1388736000, 1388995200, 1389081600, 1389168000, 1389254400,
                              1389340800, 1389600000, 1389686400, 1389772800, 1389859200, 1389945600, 1390204800,
                              1390291200, 1390377600, 1390464000, 1390550400, 1390809600, 1390896000, 1390982400,
                              1391068800, 1391155200]
        result = daily_rule.compute(return_as=turoboro.POSIX)
        self.assertEqual(result.all, expected_all_posix)

        # 5. Lets change to every third day, until March 31th 2014, excepting weekends and February
        daily_rule.every_nth_day(3).except_months(turoboro.FEBRUARY).end_on(datetime(2014, 3, 31))
        expected_all = ['2014-01-01T08:00:00', '2014-01-07T08:00:00', '2014-01-10T08:00:00', '2014-01-13T08:00:00',
                        '2014-01-16T08:00:00', '2014-01-22T08:00:00', '2014-01-28T08:00:00', '2014-01-31T08:00:00',
                        '2014-03-05T08:00:00', '2014-03-11T08:00:00', '2014-03-14T08:00:00', '2014-03-17T08:00:00',
                        '2014-03-20T08:00:00', '2014-03-26T08:00:00']

        result = daily_rule.compute()
        self.assertEqual(result.all, expected_all)

        # 6. Lets get a segment out of our result
        expected_segment = ['2014-01-31T08:00:00', '2014-03-05T08:00:00', '2014-03-11T08:00:00', '2014-03-14T08:00:00',
                            '2014-03-17T08:00:00', '2014-03-20T08:00:00', '2014-03-26T08:00:00']
        self.assertEqual(result.segment(datetime(2014, 1, 31)), expected_segment)
        self.assertEqual(result.segment(datetime(2014, 3, 27)), [])
        expected_segment = ['2014-01-22T08:00:00', '2014-01-28T08:00:00', '2014-01-31T08:00:00',
                            '2014-03-05T08:00:00', '2014-03-11T08:00:00']
        self.assertEqual(result.segment(datetime(2014, 1, 20), datetime(2014, 3, 12)), expected_segment)

    def test_staggered(self):
        daily_rule = turoboro.DailyRule(
            datetime(2014, 1, 1), end_on=datetime(2014, 12, 31), every_nth_day=7, except_weekdays=turoboro.WEEKEND,
            except_months=(turoboro.FEBRUARY, turoboro.OCTOBER), on_hour=14)

        expected_all = ['2014-01-01T14:00:00', '2014-01-08T14:00:00', '2014-01-15T14:00:00', '2014-01-22T14:00:00',
                        '2014-01-29T14:00:00', '2014-03-05T14:00:00', '2014-03-12T14:00:00', '2014-03-19T14:00:00',
                        '2014-03-26T14:00:00', '2014-04-02T14:00:00', '2014-04-09T14:00:00', '2014-04-16T14:00:00',
                        '2014-04-23T14:00:00', '2014-04-30T14:00:00', '2014-05-07T14:00:00', '2014-05-14T14:00:00',
                        '2014-05-21T14:00:00', '2014-05-28T14:00:00', '2014-06-04T14:00:00', '2014-06-11T14:00:00',
                        '2014-06-18T14:00:00', '2014-06-25T14:00:00', '2014-07-02T14:00:00', '2014-07-09T14:00:00',
                        '2014-07-16T14:00:00', '2014-07-23T14:00:00', '2014-07-30T14:00:00', '2014-08-06T14:00:00',
                        '2014-08-13T14:00:00', '2014-08-20T14:00:00', '2014-08-27T14:00:00', '2014-09-03T14:00:00',
                        '2014-09-10T14:00:00', '2014-09-17T14:00:00', '2014-09-24T14:00:00', '2014-11-05T14:00:00',
                        '2014-11-12T14:00:00', '2014-11-19T14:00:00', '2014-11-26T14:00:00', '2014-12-03T14:00:00',
                        '2014-12-10T14:00:00', '2014-12-17T14:00:00', '2014-12-24T14:00:00', '2014-12-31T14:00:00']

        result = daily_rule.compute()
        self.assertEqual(expected_all, result.all)
        result_staggered = daily_rule.compute(from_dt=datetime(2014, 5, 29))
        self.assertEqual(result_staggered.first, '2014-06-04T14:00:00')
        self.assertEqual(result_staggered.last, '2014-12-31T14:00:00')
        self.assertEqual(result_staggered.count, 26)
        result_staggered = daily_rule.compute(from_dt=datetime(2014, 11, 23))
        self.assertEqual(result_staggered.first, '2014-11-26T14:00:00')
        self.assertEqual(result_staggered.last, '2014-12-31T14:00:00')
        self.assertEqual(result_staggered.count, 6)

    def test_half_year(self):
        daily_rule = turoboro.DailyRule(start=datetime(2014, 1, 1), end_on=datetime(2020, 12, 31), every_nth_day=183,
                                        except_weekdays=turoboro.WEEKEND)
        expected_half_year_results = ['2014-01-01T00:00:00', '2014-07-03T00:00:00', '2015-01-02T00:00:00',
                                      '2016-07-04T00:00:00', '2017-01-03T00:00:00', '2017-07-05T00:00:00',
                                      '2018-01-04T00:00:00', '2018-07-06T00:00:00', '2020-01-06T00:00:00',
                                      '2020-07-07T00:00:00']
        self.assertEqual(expected_half_year_results, daily_rule.compute().all)


class DailyRuleWithRepeatNTimesTests(unittest.TestCase):
    def test(self):
        daily_rule = turoboro.DailyRule(datetime(2014, 1, 1), repeat_n_times=10, except_weekdays=turoboro.WEEKEND,
                                        on_hour=8)
        expected  = ['2014-01-01T08:00:00', '2014-01-02T08:00:00', '2014-01-03T08:00:00', '2014-01-06T08:00:00',
                     '2014-01-07T08:00:00', '2014-01-08T08:00:00', '2014-01-09T08:00:00', '2014-01-10T08:00:00',
                     '2014-01-13T08:00:00', '2014-01-14T08:00:00']
        result = daily_rule.compute()
        self.assertEqual(result.first, '2014-01-01T08:00:00')
        self.assertEqual(result.last, '2014-01-14T08:00:00')
        self.assertEqual(result.count, 10)
        self.assertEqual(expected, result.all)

        # Lets change to every third day, until March 31th 2014, excepting weekends and February
        daily_rule.every_nth_day(3).except_months(turoboro.FEBRUARY).repeat_n_times(15)
        expected_all = ['2014-01-01T08:00:00', '2014-01-07T08:00:00', '2014-01-10T08:00:00', '2014-01-13T08:00:00',
                        '2014-01-16T08:00:00', '2014-01-22T08:00:00', '2014-01-28T08:00:00', '2014-01-31T08:00:00',
                        '2014-03-05T08:00:00', '2014-03-11T08:00:00', '2014-03-14T08:00:00', '2014-03-17T08:00:00',
                        '2014-03-20T08:00:00', '2014-03-26T08:00:00', '2014-04-01T08:00:00']
        result = daily_rule.compute()
        self.assertEqual(expected_all, result.all)

        # Lets get a segment out of our result
        expected_segment = ['2014-01-31T08:00:00', '2014-03-05T08:00:00', '2014-03-11T08:00:00', '2014-03-14T08:00:00',
                            '2014-03-17T08:00:00', '2014-03-20T08:00:00', '2014-03-26T08:00:00', '2014-04-01T08:00:00']
        self.assertEqual(result.segment(datetime(2014, 1, 31)), expected_segment)
        self.assertEqual(result.segment(datetime(2014, 4, 2)), [])
        expected_segment = ['2014-01-22T08:00:00', '2014-01-28T08:00:00', '2014-01-31T08:00:00',
                            '2014-03-05T08:00:00', '2014-03-11T08:00:00']
        self.assertEqual(result.segment(datetime(2014, 1, 20), datetime(2014, 3, 12)), expected_segment)

    def test_staggered(self):
        daily_rule = turoboro.DailyRule(
            datetime(2014, 1, 1), repeat_n_times=44, every_nth_day=7, except_weekdays=turoboro.WEEKEND,
            except_months=(turoboro.FEBRUARY, turoboro.OCTOBER), on_hour=14)

        expected_all = ['2014-01-01T14:00:00', '2014-01-08T14:00:00', '2014-01-15T14:00:00', '2014-01-22T14:00:00',
                        '2014-01-29T14:00:00', '2014-03-05T14:00:00', '2014-03-12T14:00:00', '2014-03-19T14:00:00',
                        '2014-03-26T14:00:00', '2014-04-02T14:00:00', '2014-04-09T14:00:00', '2014-04-16T14:00:00',
                        '2014-04-23T14:00:00', '2014-04-30T14:00:00', '2014-05-07T14:00:00', '2014-05-14T14:00:00',
                        '2014-05-21T14:00:00', '2014-05-28T14:00:00', '2014-06-04T14:00:00', '2014-06-11T14:00:00',
                        '2014-06-18T14:00:00', '2014-06-25T14:00:00', '2014-07-02T14:00:00', '2014-07-09T14:00:00',
                        '2014-07-16T14:00:00', '2014-07-23T14:00:00', '2014-07-30T14:00:00', '2014-08-06T14:00:00',
                        '2014-08-13T14:00:00', '2014-08-20T14:00:00', '2014-08-27T14:00:00', '2014-09-03T14:00:00',
                        '2014-09-10T14:00:00', '2014-09-17T14:00:00', '2014-09-24T14:00:00', '2014-11-05T14:00:00',
                        '2014-11-12T14:00:00', '2014-11-19T14:00:00', '2014-11-26T14:00:00', '2014-12-03T14:00:00',
                        '2014-12-10T14:00:00', '2014-12-17T14:00:00', '2014-12-24T14:00:00', '2014-12-31T14:00:00']

        result = daily_rule.compute()
        self.assertEqual(expected_all, result.all)
        result_staggered = daily_rule.compute(from_dt=datetime(2014, 5, 29))
        self.assertEqual(result_staggered.count, 26)
        self.assertEqual(result_staggered.first, '2014-06-04T14:00:00')
        self.assertEqual(result_staggered.last, '2014-12-31T14:00:00')
        result_staggered = daily_rule.compute(from_dt=datetime(2014, 11, 23))
        self.assertEqual(result_staggered.first, '2014-11-26T14:00:00')
        self.assertEqual(result_staggered.last, '2014-12-31T14:00:00')
        self.assertEqual(result_staggered.count, 6)

    def test_next(self):
        daily_rule = turoboro.DailyRule(
            datetime(2014, 1, 1), repeat_n_times=44, every_nth_day=7, except_weekdays=turoboro.WEEKEND,
            except_months=(turoboro.FEBRUARY, turoboro.OCTOBER), on_hour=14
        )
        result = daily_rule.result()
        self.assertEqual(next(result), '2014-01-01T14:00:00')
        self.assertEqual(next(result), '2014-01-08T14:00:00')


class DailyInfiniteRuleTests(unittest.TestCase):
    def test(self):
        daily_rule = turoboro.DailyRule(datetime(2014, 1, 1), every_nth_day=5, except_weekdays=turoboro.WEEKEND,
                                        on_hour=8)
        result = daily_rule.compute()
        self.assertTrue(result.infinite)
        self.assertEqual(result.count, 100)
        self.assertEqual(result.first, '2014-01-01T08:00:00')
        self.assertEqual(result.last, '2015-11-27T08:00:00')

        result = daily_rule.compute(datetime(2015, 11, 27), max_count_if_infinite=20)
        self.assertTrue(result.infinite)
        self.assertEqual(result.count, 20)
        self.assertEqual(result.first, '2015-12-02T08:00:00')
        self.assertEqual(result.last, '2016-04-15T08:00:00')

    def test_next(self):
        daily_rule = turoboro.DailyRule(
            datetime(2014, 1, 1), every_nth_day=7, except_weekdays=turoboro.WEEKEND,
            except_months=(turoboro.FEBRUARY, turoboro.OCTOBER), on_hour=14
        )

        result = daily_rule.result(datetime.utcnow())
        for res in result:
            daily_rule._is_allowed(turoboro.common.datetime_from_isoformat(res))
