from datetime import datetime
import turoboro


class Result(object):
    def __init__(self, datetimes, rule, infinite=False, segment_from=None, return_as=turoboro.ISO):
        self.datetimes = datetimes
        self.rule = rule
        self.infinite = infinite
        self.return_as = return_as
        if segment_from is not None and isinstance(segment_from, datetime):
            self.datetimes = self._raw_segment(segment_from)

    @property
    def count(self):
        return len(self.datetimes)

    @property
    def first(self):
        if self.datetimes:
            return self.rule.repr_dt(self.datetimes[0], self.return_as, self.rule.timezone)

        return None

    @property
    def last(self):
        if self.datetimes:
            return self.rule.repr_dt(self.datetimes[-1], self.return_as, self.rule.timezone)

        return None

    @property
    def all(self):
        return self.formatted_list(self.datetimes)

    def formatted_list(self, _list):
        return [
            self.rule.repr_dt(n, self.return_as, self.rule.timezone) for n in _list
        ]

    def _raw_segment(self, _from, to=None):
        if _from.tzinfo is None:
            _from = self.rule.timezone.localize(_from)
        if to is not None and to.tzinfo is None:
            to = self.rule.timezone.localize(to)
        if isinstance(_from, datetime):
            if to is None:
                return [dt for dt in self.datetimes if dt >= _from]
            return [dt for dt in self.datetimes if to >= dt >= _from]

        return []

    def segment(self, _from, to=None):
        return self.formatted_list(self._raw_segment(_from, to))