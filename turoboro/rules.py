from datetime import datetime, timedelta
import abc
import voluptuous
import turoboro.common
import turoboro.constants
from copy import deepcopy


class Result(object):
    def __init__(self, datetimes, infinite=False, return_as=turoboro.ISO):
        self.datetimes = datetimes
        self.infinite = infinite
        self.return_as = return_as

    @property
    def count(self):
        return len(self.datetimes)

    @property
    def first(self):
        if self.datetimes:
            return turoboro.common.convert_datetime_to(self.datetimes[0], self.return_as)

        return None

    @property
    def last(self):
        if self.datetimes and not self.infinite:
            return turoboro.common.convert_datetime_to(self.datetimes[-1], self.return_as)

        return None

    @property
    def all(self):
        return self.formatted_list(self.datetimes)

    def formatted_list(self, _list):
        return [
            turoboro.common.convert_datetime_to(n, self.return_as) for n in _list
        ]

    def segment(self, _from, to=None):
        if isinstance(_from, datetime):
            if to is None:
                return self.formatted_list([
                    dt for dt in self.datetimes if dt >= _from
                ])
            return self.formatted_list([dt for dt in self.datetimes if to >= dt >= _from])

        return []


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

