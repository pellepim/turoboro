import abc
import turoboro.common
import turoboro.constants
from copy import deepcopy
import pytz
from datetime import timedelta
import json

# <PYTHON2COMPATIBILITY>
try:
    RecursionError()
except:
    RecursionError = RuntimeError


class abstractclassmethod(classmethod):

    __isabstractmethod__ = True

    def __init__(self, callable):
        callable.__isabstractmethod__ = True
        super(abstractclassmethod, self).__init__(callable)
# </PYTHON2COMPATIBILITY>


class Rule:
    __metaclass__ = abc.ABCMeta

    @property
    def spec(self):
        return getattr(self, '_spec', {})

    def __repr__(self):
        return json.dumps(self.spec, sort_keys=True)

    @spec.setter
    def spec(self, spec):
        setattr(self, '_spec', self.validate_spec(spec))

    @property
    def timezone(self):
        return pytz.timezone(self.spec['timezone'])

    @abc.abstractmethod
    def compute(self, from_dt=None, max_count_if_infinite=100, return_as=turoboro.ISO):
        pass

    @abc.abstractmethod
    def validate_spec(self, spec):
        pass

    @abstractclassmethod
    def factory(cls, spec):
        pass

    def set_if_valid(self, field, value):
        spec = deepcopy(self.spec)
        spec[field] = value
        self.validate_spec(spec)
        self.spec = spec

    def repeat_n_times(self, n):
        """
        Where `n` is the number of times that the rule should repeat. Cannot be specified along with an end date
        for the rule.
        :param n: An integer specifying the number of times the rule should repeat
        :type n: int
        :return: turoboro.rules.DailyRule
        """
        self.set_if_valid('repeat', n)
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
        self.spec['start'] = self.start_datetime.replace(hour=hour).isoformat()
        if self.spec['end'] is not None:
            self.spec['end'] = self.end_datetime.replace(hour=hour).isoformat()
        return self

    def _end_before(self, end):
        """
        The last occurrence of the recurring rule should fall before this specified date.
        :param end: A datetime specifying the last day that the rule is valid before.
        :type end: datetime | None
        :return: turoboro.rules.DailyRule
        """
        if end is None:
            self.set_if_valid('end', None)
            return self
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
        end = end.replace(hour=self.spec['on_hour'], minute=0, second=0, microsecond=0)
        if end.tzinfo is None:
            end = self.timezone.localize(end)
        self._end_before(end + timedelta(days=1))
        return self

    @property
    def start_datetime(self):
        dt = turoboro.common.datetime_from_isoformat(self.spec['start'])
        return self.timezone.localize(dt)

    @property
    def end_datetime(self):
        if self.spec['end'] is not None:
            dt = turoboro.common.datetime_from_isoformat(self.spec['end'])
            return self.timezone.localize(dt)
        return None

    @classmethod
    def repr_dt(cls, dt, to=turoboro.ISO, timezone=pytz.UTC):
        try:
            localized_dt = timezone.localize(dt)
        except ValueError:  # dt is probably already localized
            localized_dt = dt
        dt = localized_dt.astimezone(pytz.UTC)
        return turoboro.common.convert_datetime_to(dt, to)

    def result(self, from_dt=None, max_count_if_infinite=3, return_as=turoboro.ISO):
        result = self.compute(from_dt=from_dt, max_count_if_infinite=max_count_if_infinite,
                              return_as=turoboro.DATETIME_INSTANCE)
        count = 0
        last_dt = None
        for dt in result.all:
            count += 1
            last_dt = dt
            yield self.repr_dt(dt, return_as, self.timezone)

        if count == len(result.all) and result.infinite:
            try:
                _r = self.result(from_dt=last_dt, max_count_if_infinite=max_count_if_infinite, return_as=return_as)
                count += 1
                for r in _r:
                    yield r
            except (RecursionError, OverflowError):
                pass

    @classmethod
    def from_spec(cls, spec):
        spec = json.loads(spec)
        if spec['rule'] == 'daily':
            return turoboro.DailyRule.factory(spec)
        if spec['rule'] == 'weekly':
            return turoboro.WeeklyRule.factory(spec)
