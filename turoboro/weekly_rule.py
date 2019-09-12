from turoboro.rules import Rule
import turoboro.common
import voluptuous
import pytz
from datetime import datetime, timedelta
from turoboro.result import Result


class WeeklyRule(Rule):
    SPEC_SCHEMA = voluptuous.Schema({
        'start': turoboro.common.is_iso_datetime,
        'end': voluptuous.Any(
            None, turoboro.common.is_iso_datetime
        ),
        'repeat': voluptuous.Any(
            None, voluptuous.All(int, voluptuous.Range(min=1))
        ),
        'rule': 'weekly',
        'every_nth_week': voluptuous.Range(min=1, max=53),
        'on_days': voluptuous.Or(
            None,
            voluptuous.All(
                turoboro.common.is_list_of_days,
                voluptuous.Length(min=1, max=7)
            )
        ),
        'except_months': voluptuous.Or(
            None,
            voluptuous.All(
                turoboro.common.is_list_of_months,
                voluptuous.Length(min=1, max=11)
            )
        ),
        'on_hour': voluptuous.Range(min=0, max=23),
        'timezone': voluptuous.In(pytz.all_timezones)
    })

    def __init__(self, start, on_days, end_on=None, repeat_n_times=None, every_nth_week=1,
                 except_months=None, on_hour=0, timezone='UTC'):
        if not isinstance(start, datetime):
            raise ValueError('You must specify a datetime')

        tz = pytz.timezone(timezone)
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        start = tz.localize(start)

        if isinstance(end_on, datetime):
            end_on = end_on.replace(hour=0, minute=0, second=0, microsecond=0)
            end_on = tz.localize(end_on)
            if end_on < start:
                raise ValueError('End cannot be before start')

        self.spec = {
            "start": start.isoformat(),
            "end": None,
            "repeat": None,
            "rule": "weekly",
            "every_nth_week": 1,
            "on_days": [0],
            "except_months": None,
            "on_hour": 0,
            "timezone": timezone
        }

        if repeat_n_times:
            self.repeat_n_times(repeat_n_times)

        self.every_nth_week(every_nth_week)

        try:
            self.on_days(*on_days)
        except TypeError:
            pass

        try:
            self.except_months(*except_months)
        except TypeError:
            pass

        self.on_hour(on_hour)

        if end_on:
            self.end_on(end_on)

    @classmethod
    def factory(cls, spec):
        daily_rule = cls(datetime.utcnow(), (0,))
        if daily_rule.validate_spec(spec):
            daily_rule.spec = spec

        return daily_rule

    def every_nth_week(self, n):
        """
        Where `n` is the number of days between two occurrences
        :param n: The number of days between two occurrences
        :type n: int
        :return: turoboro.rules.DailyRule
        """
        self.set_if_valid('every_nth_week', n)
        return self

    def on_days(self, *days):
        """
        Where `days` is a tuple of weekdays from 0 to 6. Where 0 is Monday. The recurring rule will include only
        these weekdays every week that's included.
        :param days: A tuple of integers, designating weekdays from 0-6 (where 0 is Monday)
        :type days: tuple | None
        :return: turoboro.rules.DailyRule
        """
        if len(days) == 1 and days[0] is None:
            days = None
        self.set_if_valid('on_days', days)
        return self

    def validate_spec(self, spec):
        """
        Validates the rule specification
        :param spec: The spec we are attempting to accept
        :type spec: dict
        :return: dict
        """
        starting_day = turoboro.common.datetime_from_isoformat(spec['start'])

        if spec['end'] is not None and spec['end'] <= spec['start']:
            raise ValueError("End date (%s) must be None or after start date (%s)" % (spec['end'], spec['start']))

        if spec['on_days'] is None:
            raise ValueError('You have to pick at least one week day')

        if spec['except_months'] is not None and starting_day.month in spec['except_months']:
            raise ValueError('You may not forbid months that include the start day')

        if spec['end'] is not None and spec['repeat'] is not None:
            raise ValueError('You may not specify both an end date and a repeat count')

        return self.SPEC_SCHEMA(spec)

    def _stagger_forward(self, from_dt):
        """
        :param from_dt: the datetime we want to stagger forward from
        :type from_dt: datetime
        :return: datetime
        """
        from_dt = from_dt.replace(hour=self.spec['on_hour'], minute=0, second=0, microsecond=0)

        # Always start on Monday
        from_dt -= timedelta(from_dt.weekday())

        period_delta = from_dt - self.timezone.localize(turoboro.common.datetime_from_isoformat(self.spec['start']))

        if period_delta.days < 0:
            return self.timezone.localize(turoboro.common.datetime_from_isoformat(self.spec['start']))

        number_of_weeks_passed_since_start = int(period_delta.days/7)
        number_of_weeks_passed_since_start += 1 if period_delta.days % 7 else 0
        pad_with_weeks = self.spec['every_nth_week'] - number_of_weeks_passed_since_start % self.spec['every_nth_week']

        from_dt = from_dt + timedelta(days=7*pad_with_weeks)

        return from_dt

    def _is_allowed(self, dt):
        if self.spec['except_months'] is not None and dt.month in self.spec['except_months']:
            return False

        if dt.weekday() not in self.spec['on_days']:
            return False

        return True

    def _compute_with_end_date(self, from_dt, working_date, return_as):
        result = []
        if from_dt is not None and from_dt != working_date:
            working_date = self._stagger_forward(from_dt)

        end_date = self.timezone.localize(turoboro.common.datetime_from_isoformat(self.spec['end']))

        while working_date < end_date:
            if self._is_allowed(working_date):
                result.append(working_date)
            working_date = self._bounce(working_date)

        return Result(result, self, return_as=return_as)

    def _compute_n_times(self, from_dt, working_date, return_as):
        result = []
        count = 0
        if from_dt is not None:
            from_dt = from_dt.replace(hour=self.spec['on_hour'], minute=0, second=0, microsecond=0)

        while count < self.spec['repeat']:
            if self._is_allowed(working_date):
                result.append(working_date)
                count += 1

            working_date = self._bounce(working_date)

        return Result(result, self, return_as=return_as, segment_from=from_dt)

    def compute(self, from_dt=None, max_count_if_infinite=100, return_as=turoboro.ISO):
        working_date = self.timezone.localize(turoboro.common.datetime_from_isoformat(self.spec['start']))

        if from_dt is not None and from_dt.tzinfo is None:
            from_dt = self.timezone.localize(from_dt)
        if self.spec['end'] is not None:
            return self._compute_with_end_date(from_dt, working_date, return_as)
        elif self.spec['repeat'] is not None:
            return self._compute_n_times(from_dt, working_date, return_as)

        return self._compute_infinite(from_dt, working_date, max_count_if_infinite, return_as)

    def _bounce(self, working_date):
        """
        Given a certain date - lets bounce ahead into the future until the next day, unless we have set every_nth_week,
        and it happens to be a Sunday, then we bounce forward every_nth_week weeks, + one day to end up on a monday.
        :param working_date:
        :type: datetime
        :return: datetime
        """
        if working_date.weekday() == turoboro.SUNDAY and self.spec['every_nth_week'] > 1:
            working_date += timedelta(days=7 * self.spec['every_nth_week'] - 6)
        working_date += timedelta(days=1)
        return working_date

    def _compute_infinite(self, from_dt, working_date, max_count, return_as):
        result = []
        count = 0
        if working_date.tzinfo is None:
            working_date = self.timezone.localize(working_date)
        if from_dt is not None and from_dt.tzinfo is None:
            from_dt = self.timezone.localize(from_dt)
        if from_dt is not None and from_dt != working_date:
            working_date = self._stagger_forward(from_dt)

        while count < max_count:
            if self._is_allowed(working_date):
                result.append(working_date)
                count += 1
            working_date = self._bounce(working_date)

        return Result(result, self, return_as=return_as, infinite=True)
