import voluptuous
from turoboro.rules import Rule, Result
import turoboro.common
from datetime import datetime, timedelta


class DailyRule(Rule):
    SPEC_SCHEMA = voluptuous.Schema({
        'start': turoboro.common.is_iso_datetime,
        'end': voluptuous.Any(
            None, turoboro.common.is_iso_datetime
        ),
        'repeat': voluptuous.Any(
            None, voluptuous.All(int, voluptuous.Range(min=1))
        ),
        'rule': 'daily',
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
        'on_hour': voluptuous.Range(min=0, max=23)
    })

    def __init__(self, start=None, end_on=None, repeat_n_times=None, every_nth_day=1, except_weekdays=None,
                 except_months=None, on_hour=0):
        if start is None:
            start = datetime.utcnow()

        if not isinstance(start, datetime):
            raise ValueError('You must specify a datetime')

        start = start.replace(hour=0, minute=0, second=0, microsecond=0)

        if isinstance(end_on, datetime):
            if end_on < start:
                raise ValueError('End cannot be before start')

            end_on = end_on.replace(hour=0, minute=0, second=0, microsecond=0)

        self.spec = {
            "start": start.isoformat(),
            "end": None,
            "repeat": None,
            "rule": "daily",
            "every_nth_day": 1,
            "except_days": None,
            "except_months": None,
            "on_hour": 0
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

    def except_months(self, *months):
        """
        Where `months` is a tuple of months from 1-12. The recurring rule will skip specified months and move on to
        the next valid occurrence.
        :param months: A tuple of ints from 1 to 12, specifying months to ignore in the recurring rule.
        :type months: tuple | None
        :return: turoboro.rules.DailyRule
        """
        if len(months) == 1 and months[0] is None:
            months = None
        self.set_if_valid('except_months', months)
        return self

    def on_hour(self, hour):
        """
        Where `hour` is the hour on the day that the rule should trigger.
        :param hour: An integer between 0 and 23
        :type hour: int
        :return: turoboro.rules.DailyRule
        """
        self.set_if_valid('on_hour', hour)
        start_date = turoboro.common.datetime_from_isoformat(self.spec['start'])
        start_date = start_date.replace(hour=hour)
        self.set_if_valid('start', start_date.isoformat())
        if self.spec['end'] is not None:
            end_date = turoboro.common.datetime_from_isoformat(self.spec['end'])
            end_date = end_date.replace(hour=hour)
            self.set_if_valid('end', end_date.isoformat())
        return self

    def end_before(self, end):
        """
        The last occurrence of the recurring rule should fall before this specified date.
        :param end: A datetime specifying the last day that the rule is valid before.
        :type end: datetime | None
        :return: turoboro.rules.DailyRule
        """
        if end is None:
            self.set_if_valid('end', None)
            return self
        end = end.replace(hour=0, minute=0, second=0, microsecond=0)
        self.set_if_valid('end', end.isoformat())
        return self

    def end_on(self, end):
        """
        The last occurrence of the recurring rule should end on this date (if this date is a valid occurrence of the
        rule).
        :param end: A datetime specifying the last day that the rule is valid.
        :type end: datetime | None
        :return: turoboro.rules.DailyRule
        """
        if end is None:
            self.set_if_valid('end', None)
            return self
        return self.end_before(end + timedelta(days=1))

    def repeat_n_times(self, n):
        """
        Where `n` is the number of times that the rule should repeat. Cannot be specified along with an end date
        for the rule.
        :param n: An integer specifying the number of times the rule should repeat
        :type n: int
        :return: turoboro.rules.DailyRule
        """
        return self.set_if_valid('repeat', n)

    def _is_allowed(self, dt):
        if self.spec['except_days'] is not None and dt.weekday() in self.spec['except_days']:
            return False

        if self.spec['except_months'] is not None and dt.month in self.spec['except_months']:
            return False

        return True

    def _stagger_forward(self, from_dt):
        from_dt = from_dt.replace(hour=self.spec['on_hour'], minute=0, second=0, microsecond=0)
        period = from_dt - turoboro.common.datetime_from_isoformat(self.spec['start'])
        rest = period.days % self.spec['every_nth_day']
        return from_dt + timedelta(days=self.spec['every_nth_day'] - rest)

    def _compute_with_enddate(self, from_dt, working_date, return_as):
        result = []
        if from_dt is not None and from_dt != working_date:
            working_date = self._stagger_forward(from_dt)
        end_date = turoboro.common.datetime_from_isoformat(self.spec['end'])
        while working_date < end_date:
            if self._is_allowed(working_date):
                result.append(working_date)
            working_date = working_date + timedelta(days=self.spec['every_nth_day'])

        return Result(result, return_as=return_as)

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

        return Result(result, return_as=return_as, segment_from=from_dt)

    def _compute_infinite(self, from_dt, working_date, max_count, return_as):
        result = []
        count = 0
        if from_dt is not None and from_dt != working_date:
            working_date = self._stagger_forward(from_dt)

        while count < max_count:
            if self._is_allowed(working_date):
                result.append(working_date)
                count += 1
            working_date = working_date + timedelta(days=self.spec['every_nth_day'])

        return Result(result, return_as=return_as, infinite=True)

    def compute(self, from_dt=None, max_count_if_infinite=100, return_as=turoboro.ISO):
        working_date = turoboro.common.datetime_from_isoformat(self.spec['start'])
        if self.spec['end'] is not None:
            return self._compute_with_enddate(from_dt, working_date, return_as)
        elif self.spec['repeat'] is not None:
            return self._compute_n_times(from_dt, working_date, return_as)

        return self._compute_infinite(from_dt, working_date, max_count_if_infinite, return_as)
