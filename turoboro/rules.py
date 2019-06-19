from datetime import datetime
import abc
import voluptuous
import turoboro.common
import turoboro.constants
from copy import deepcopy


class Rule(object, metaclass=abc.ABCMeta):
    @property
    def spec(self):
        return getattr(self, '_spec', {})

    @spec.setter
    def spec(self, spec):
        setattr(self, '_spec', self.validate_spec(spec))

    @abc.abstractmethod
    def compute(self):
        pass

    @abc.abstractmethod
    def validate_spec(self, spec):
        pass

    def set_if_valid(self, field, value):
        spec = deepcopy(self.spec)
        spec[field] = value
        self.validate_spec(spec)
        self.spec = spec


class DailyRule(Rule):
    SPEC_SCHEMA = voluptuous.Schema({
        'start': turoboro.common.is_iso_datetime,
        'end': voluptuous.Any(
            None, turoboro.common.is_iso_datetime
        ),
        'rule': 'daily',
        'repeat': voluptuous.Range(min=1, max=7),
        'exceptDays': voluptuous.Or(
            None,
            voluptuous.All(
                turoboro.common.is_list_of_days,
                voluptuous.Length(min=1, max=6)
            )
        ),
        'exceptMonths': voluptuous.Or(
            None,
            voluptuous.All(
                turoboro.common.is_list_of_months,
                voluptuous.Length(min=1, max=11)
            )
        ),
        'hour': voluptuous.Range(min=0, max=23)
    })

    def __init__(self, start=None):
        if start is None:
            start = datetime.utcnow()

        if not isinstance(start, datetime):
            raise RuntimeError('You must specify a datetime')

        self.spec = {
            "start": start.isoformat(),
            "rule": "daily",
            "repeat": 1,
            "exceptDays": None,
            "exceptMonths": None,
            "hour": 0
        }

    def validate_spec(self, spec):
        return self.SPEC_SCHEMA(spec)

    def compute(self):
        pass

    def repeat(self, day_interval):
        self.set_if_valid('repeat', day_interval)
        return self

    def except_days(self, days):
        self.set_if_valid('exceptDays', days)
        return self

    def except_months(self, months):
        self.set_if_valid('exceptMonths', months)
        return self

    def hour(self, hour):
        self.set_if_valid('hour', hour)
        return self
