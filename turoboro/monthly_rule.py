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

    def compute(self, from_dt=None, max_count_if_infinite=100, return_as=turoboro.ISO):
        pass
