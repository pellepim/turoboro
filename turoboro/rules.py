from datetime import datetime, timedelta
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
    def compute(self, starting_at=None, count=None):
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

    def __init__(self, start=None, end=None):
        if start is None:
            start = datetime.utcnow()

        if not isinstance(start, datetime):
            raise RuntimeError('You must specify a datetime')

        start = start.replace(hour=0, minute=0, second=0, microsecond=0)

        if isinstance(end, datetime):
            if end < start:
                raise ValueError('End cannot be before start')

            end = end.replace(hour=0, minute=0, second=0, microsecond=0)

        self.spec = {
            "start": start.isoformat(),
            "end": end.isoformat() if isinstance(end, datetime) else None,
            "rule": "daily",
            "repeat": 1,
            "exceptDays": None,
            "exceptMonths": None,
            "hour": 0
        }

    def validate_spec(self, spec):
        if spec['end'] is not None and spec['end'] < spec['start']:
            raise ValueError("End date (%s) must be None or after start date (%s)" % (spec['end'], spec['start']))

        return self.SPEC_SCHEMA(spec)

    def _chain_compute(self, starting_at, count, return_as):
        def should_continue(_n, _c):
            if count == -1 and self.spec['end']:
                return _n < turoboro.common.datetime_from_isoformat(self.spec['end'])
            return _c < count

        if count == -1 and self.spec['end'] is None:
            raise RuntimeError('Cannot ask for all if end date is unspecified')

        current_count = 1
        _next = self.compute(starting_at, return_as=turoboro.DATETIME_INSTANCE, in_chain=True)
        results = [_next]
        while should_continue(_next, current_count):
            _next = self.compute(_next, return_as=turoboro.DATETIME_INSTANCE, in_chain=True)
            results.append(_next)
            current_count += 1

        return [turoboro.common.convert_datetime_to(n, return_as) for n in results if self._is_allowed(n)]

    def _is_allowed(self, dt):
        if self.spec['exceptDays'] is not None and dt.weekday() in self.spec['exceptDays']:
            return False

        if self.spec['exceptMonths'] is not None and dt.month in self.spec['exceptMonths']:
            return False

        if self.spec['end'] is not None and dt > turoboro.common.datetime_from_isoformat(self.spec['end']):
            return False

        return True

    def _stagger_back(self, provisional_start_date):
        delta = provisional_start_date - turoboro.common.datetime_from_isoformat(self.spec['start'])
        rest = delta.days % self.spec['repeat']
        return provisional_start_date - timedelta(days=rest)

    def compute(self, starting_at=None, count=None, return_as=turoboro.ISO, in_chain=False):
        if starting_at is None or starting_at < turoboro.common.datetime_from_isoformat(self.spec['start']):
            starting_at = turoboro.common.datetime_from_isoformat(self.spec['start'])

        if not in_chain and starting_at != turoboro.common.datetime_from_isoformat(self.spec['start']):
            starting_at = self._stagger_back(starting_at)

        if count is not None and isinstance(count, int):
            return self._chain_compute(starting_at, count, return_as)

        starting_at = starting_at.replace(hour=self.spec['hour'], minute=0)

        next = starting_at + timedelta(days=(self.spec['repeat']))

        if not in_chain and not self._is_allowed(next):
            return None

        return turoboro.common.convert_datetime_to(next, return_as)

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

    def end(self, end):
        if end is None or (isinstance(end, datetime) and end > turoboro.common.datetime_from_isoformat(self.spec['start'])):
            end = end.replace(hour=0, minute=0, second=0, microsecond=0)
            return self.set_if_valid('end', end.isoformat())

        raise ValueError("End date (%s) must be None or after start date (%s)" % (end, self.spec['start']))
