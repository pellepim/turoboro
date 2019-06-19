from datetime import datetime
import abc
import voluptuous
import turoboro.common
import turoboro.constants


class Rule(object, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_spec(self):
        pass

    @abc.abstractmethod
    def set_spec(self, spec):
        pass

    @abc.abstractmethod
    def compute(self):
        pass

    @abc.abstractmethod
    def validate_spec(self, spec):
        pass


class DailyRule(Rule):
    SPEC_SCHEMA = voluptuous.Schema({
        'start': turoboro.common.is_iso_datetime,
        'end': voluptuous.Any(
            None, turoboro.common.is_iso_datetime
        ),
        'rule': 'daily',
        'repeat': voluptuous.Range(min=1, max=7),
        'except_days': voluptuous.Any(
            None, turoboro.common.is_list_of_days
        ),
        'except_months': voluptuous.Any(
            None, turoboro.common.is_list_of_months
        )
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
            "exceptWeekdays": None,
            "exceptMonths": None
        }

    def get_spec(self):
        return self.spec

    def set_spec(self, spec):
        self.spec = self.validate_spec(spec)

    def validate_spec(self, spec):
        return self.SPEC_SCHEMA(spec)

    def compute(self):
        pass




