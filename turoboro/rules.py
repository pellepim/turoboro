import abc
import turoboro.common
import turoboro.constants
from copy import deepcopy
import pytz


class Rule:
    __metaclass__ = abc.ABCMeta

    @property
    def spec(self):
        return getattr(self, '_spec', {})

    @spec.setter
    def spec(self, spec):
        setattr(self, '_spec', self.validate_spec(spec))

    @property
    def timezone(self):
        return pytz.timezone(self.spec['timezone'])

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

    def repr_dt(self, dt, to=turoboro.ISO, timezone=pytz.UTC):
        try:
            localized_dt = timezone.localize(dt)
        except ValueError:  # dt is probably already localized
            localized_dt = dt
        dt = localized_dt.astimezone(pytz.UTC)
        return turoboro.common.convert_datetime_to(dt, to)
