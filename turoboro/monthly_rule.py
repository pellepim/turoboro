from turoboro.rules import Rule
import turoboro.common
import voluptuous
import pytz
from datetime import datetime, timedelta
from turoboro.result import Result


class MonthlyRule(Rule):
    WEEKDAY_COUNT_SCHEMA = voluptuous.Schema({
        'count': voluptuous.All(int, voluptuous.Range(min=1, max=5)),
        'weekday': voluptuous.Any(voluptuous.Range(min=turoboro.MONDAY, max=turoboro.SUNDAY)),
        'every_nth': voluptuous.All(int, voluptuous.Range(min=1, max=12))
    })
    DAY_OF_MONTH_RULE = voluptuous.Schema({
        'day': voluptuous.All(int, voluptuous.Range(min=1, max=31)),
        'every_nth': voluptuous.All(int, voluptuous.Range(min=1, max=12))
    })
    SPEC_SCHEMA = voluptuous.Schema({
        'start': turoboro.common.is_iso_datetime,
        'end': voluptuous.Any(
            None, turoboro.common.is_iso_datetime
        ),
        'repeat': voluptuous.Any(
            None, voluptuous.All(int, voluptuous.Range(min=1))
        ),
        'rule': 'monthly',
        'day_of_month_rule': voluptuous.Any(None, DAY_OF_MONTH_RULE),
        'weekday_rule': voluptuous.Any(None, WEEKDAY_COUNT_SCHEMA),
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

    def __init__(self, start, day_of_month=None, every_nth_month=None, end_on=None, repeat_n_times=None, weekday_count=None, weekday=None,
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
            'start': start.isoformat(),
            'end': None,
            'repeat': None,
            'rule': 'monthly',
            'day_of_month_rule': {
                'day': 1,
                'every_nth': 1
            },
            'weekday_rule': None,
            'except_months': None,
            'on_hour': on_hour,
            'timezone': timezone
        }

        if day_of_month:
            self.day_of_month(day_of_month, every_nth_month)
        elif weekday_count and weekday:
            self.weekday(weekday_count, weekday, every_nth_month)
        else:
            raise ValueError('You must specify either day of month, or weekday_count and weekday')

        try:
            self.except_months(*except_months)
        except TypeError:
            pass

        self.on_hour(on_hour)

        if end_on:
            self.end_on(end_on)

    def day_of_month(self, day_of_month, every_nth_month=None):
        self.set_if_valid('day_of_month_rule', {
            'day': day_of_month, 'every_nth': 1 if every_nth_month is None else every_nth_month
        })
        self.set_if_valid('weekday_rule', None)
        return self

    def weekday(self, weekday_count, weekday, every_nth_month=None):
        self.set_if_valid('weekday_rule', {
            'count': weekday_count,
            'weekday': weekday,
            'every_nth': 1 if every_nth_month is None else every_nth_month
        })
        self.set_if_valid('day_of_month_rule', None)
        return self

    @classmethod
    def factory(cls, spec):
        weekly_rule = cls(datetime.utcnow(), (0,))
        if weekly_rule.validate_spec(spec):
            weekly_rule.spec = spec

        return weekly_rule

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

        if spec['day_of_month_rule'] is None and spec['weekday_rule'] is None:
            raise ValueError('You must specify either day of month, or weekday_count and weekday')

        if spec['except_months'] is not None and starting_day.month in spec['except_months']:
            raise ValueError('You may not forbid months that include the start day')

        if spec['end'] is not None and spec['repeat'] is not None:
            raise ValueError('You may not specify both an end date and a repeat count')

        return self.SPEC_SCHEMA(spec)

    def _day_of_month_stagger(self, from_dt, start_dt):
        start_dt_calc = (start_dt.year, start_dt.month)
        from_dt_calc = (from_dt.year, from_dt.month)

        months = (from_dt_calc[0] - start_dt_calc[0]) * 12 + from_dt_calc[1] - start_dt_calc[1]

        # We've a from date before the earliest possible start date - return that instead
        if months < 0:
            return self.timezone.localize(turoboro.common.datetime_from_isoformat(self.spec['start']))

        rest = months % self.spec['day_of_month_rule']['every_nth']

        # No rest - we're already in the correct month, if we have not passed the day - we return the day
        if rest == 0 and from_dt.day <= self.spec['day_of_month_rule']['day']:
            return from_dt.replace(day=self.spec['day_of_month_rule']['day'])

        month_pad = rest - self.spec['day_of_month_rule']['every_nth']

        # If we pass a new year, we need to pad the year
        stagger_to_year = from_dt.year + 1 if from_dt.month + month_pad > 12 else from_dt.year
        # If we pass a new year, we need to stagger forward months - 12,
        stagger_to_month = from_dt.month + month_pad - 12 if stagger_to_year > from_dt.year else from_dt.month + month_pad

        return from_dt.replace(year=stagger_to_year, month=stagger_to_month, day=1)

    def _stagger_forward(self, from_dt):
        """
        :param from_dt: the datetime we want to stagger forward from
        :type from_dt: datetime
        :return: datetime
        """
        from_dt = from_dt.replace(hour=self.spec['on_hour'], minute=0, second=0, microsecond=0)

        start_dt = self.timezone.localize(turoboro.common.datetime_from_isoformat(self.spec['start']))
        start_dt = start_dt.replace(day=1, hour=self.spec['on_hour'])

        # 1. Day of month:
        if self.spec['day_of_month_rule'] is not None:
            return self._day_of_month_stagger(from_dt, start_dt)

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
        pass

    def _stagger_forward(self, from_dt):
        pass

    def _is_allowed(self, working_date):
        pass

    def _bounce(self, working_date):
        pass

