import voluptuous
from turoboro.rules import Rule
from turoboro.result import Result
import turoboro.common
from datetime import datetime, timedelta
import pytz


class DailyRule(Rule):
    SPEC_SCHEMA = voluptuous.Schema({
        'start': turoboro.common.is_iso_datetime,
        'end': voluptuous.Any(
            None, turoboro.common.is_iso_datetime
        ),
        'repeat': voluptuous.Any(
            None, voluptuous.All(int, voluptuous.Range(min=1))
        ),
        'rule': turoboro.RULE_DAILY,
        'every_nth_day': voluptuous.Range(min=1, max=365),
        'except_days': voluptuous.Or(
            None,
            voluptuous.All(
                turoboro.common.is_list_of_days,
                voluptuous.Length(min=1, max=6)
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

    def __init__(self, start, end_on=None, repeat_n_times=None, every_nth_day=1, except_weekdays=None,
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
            "rule": "daily",
            "every_nth_day": 1,
            "except_days": None,
            "except_months": None,
            "on_hour": 0,
            "timezone": timezone
        }

        if repeat_n_times:
            self.repeat_n_times(repeat_n_times)

        self.every_nth_day(every_nth_day)

        try:
            self.except_weekdays(*except_weekdays)
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
        daily_rule = cls(datetime.utcnow())
        if daily_rule.validate_spec(spec):
            daily_rule.spec = spec

        return daily_rule

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

        if spec['except_days'] is not None and starting_day.weekday() in spec['except_days']:
            raise ValueError('You may not forbid days that include the start day.')

        if spec['except_months'] is not None and starting_day.month in spec['except_months']:
            raise ValueError('You may not forbid months that include the start day')

        if spec['end'] is not None and spec['repeat'] is not None:
            raise ValueError('You may not specify both an end date and a repeat count')

        return self.SPEC_SCHEMA(spec)

    def every_nth_day(self, n):
        """
        Where `n` is the number of days between two occurrences
        :param n: The number of days between two occurrences
        :type n: int
        :return: turoboro.rules.DailyRule
        """
        self.set_if_valid('every_nth_day', n)
        return self

    def except_weekdays(self, *days):
        """
        Where `days` is a tuple of weekdays from 0 to 6. Where 0 is Monday. The recurring rule will skip specified
        weekdays and move on to the next valid occurrence.
        :param days: A tuple of integers, designating weekdays from 0-6 (where 0 is Monday)
        :type days: tuple | None
        :return: turoboro.rules.DailyRule
        """
        if len(days) == 1 and days[0] is None:
            days = None
        self.set_if_valid('except_days', days)
        return self

    def _is_allowed(self, dt):
        if self.spec['except_days'] is not None and dt.weekday() in self.spec['except_days']:
            return False

        if self.spec['except_months'] is not None and dt.month in self.spec['except_months']:
            return False

        return True

    def _stagger_forward(self, from_dt):
        from_dt = from_dt.replace(hour=self.spec['on_hour'], minute=0, second=0, microsecond=0)
        period = from_dt - self.timezone.localize(turoboro.common.datetime_from_isoformat(self.spec['start']))
        rest = period.days % self.spec['every_nth_day']
        return from_dt + timedelta(days=self.spec['every_nth_day'] - rest)

    def _compute_with_end_date(self, from_dt, working_date, return_as):
        result = []
        if from_dt is not None and from_dt != working_date:
            working_date = self._stagger_forward(from_dt)
        end_date = self.timezone.localize(turoboro.common.datetime_from_isoformat(self.spec['end']))
        while working_date < end_date:
            if self._is_allowed(working_date):
                result.append(working_date)
            working_date = working_date + timedelta(days=self.spec['every_nth_day'])

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
            working_date = working_date + timedelta(days=self.spec['every_nth_day'])

        return Result(result, self, return_as=return_as, segment_from=from_dt)

    def _bounce(self, working_date):
        return working_date + timedelta(days=self.spec['every_nth_day'])

