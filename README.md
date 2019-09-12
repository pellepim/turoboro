[![CircleCI](https://circleci.com/gh/pellepim/turoboro.svg?style=shield)](https://circleci.com/gh/pellepim/turoboro)
![Code coverage](coverage.svg "Code coverage")
# turoboro
A python library for specifying recurring time rules and getting timestamps in return.

Typical usage would be to articulate the behaviour of recurring rules and to get exact points
in time where those rules ought to be executed.

I.e this library answers the following questions: 

Given a recurring rule,

1. when is the next time it happens?
2. when are all of the times it happens?
3. when are `n` times it happens?

Say for example you want to find out at what specific UTC time the rule "every thursday of every
third week of every second month at 8 o'clock UTC" would happen.

Ask turoboro! 

However, this is very much work in progress. So... basically don't use this library yet.

# Installation

    $ pip install turoboro
    
# Usage

turoboro allows you to set up recurring rules of three main times:

1. With an end-date, or
2. that end after a certain number of occurrences, or
3. that are infinite.

All recurring rules must have a start `datetime` (defaults to now).

Lets go through them one at a time.

## Daily rule examples

    >>> import turoboro
    >>> from datetime import datetime
    >>> rule = turoboro.DailyRule(start=datetime(2014, 1, 1))
    >>> rule
    {"end": null, "every_nth_day": 1, "except_days": null, "except_months": null, "on_hour": 0, "repeat": null, "rule": "daily", "start": "2014-01-01T00:00:00+00:00", "timezone": "UTC"}
    >>> rule.every_nth_day(2).on_hour(8)
    {"end": null, "every_nth_day": 2, "except_days": null, "except_months": null, "on_hour": 8, "repeat": null, "rule": "daily", "start": "2014-01-01T08:00:00+00:00", "timezone": "UTC"}
    >>> rule.except_weekdays(*turoboro.WEEKEND)
    {"end": null, "every_nth_day": 2, "except_days": [5, 6], "except_months": null, "on_hour": 8, "repeat": null, "rule": "daily", "start": "2014-01-01T08:00:00+00:00", "timezone": "UTC"}
    >>> rule.end_on(datetime(2014, 1, 31))
    {"end": "2014-02-01T00:00:00+00:00", "every_nth_day": 2, "except_days": [5, 6], "except_months": null, "on_hour": 8, "repeat": null, "rule": "daily", "start": "2014-01-01T08:00:00+00:00", "timezone": "UTC"}
 
Alright, now we have an instance of the `DailyRule` class.

You can also instantiate the exact same thing using only a constructor:

    >>> rule = turoboro.DailyRule(
    ...     datetime(2014, 1, 1), every_nth_day=2, except_weekdays=turoboro.WEEKEND,
    ...     end_on=datetime(2014, 1, 31), on_hour=8
    ... )

Or with a factory method using the "pure" json spec:

    >>> rule = turoboro.Rule.from_json_spec({
        "end": "2014-02-01T00:00:00+00:00",
        "every_nth_day": 2,
        "except_days": [5, 6],
        "except_months": null,
        "on_hour": 8,
        "repeat": null,
        "rule": "daily",
        "start": "2014-01-01T08:00:00+00:00",
        "timezone": "UTC"
    })
    

Lets see what actual times this resolves to.

    >>> computed = rule.compute()
    >>> computed.first
    '2014-01-01T08:00:00'
    >>> computed.last
    '2014-01-31T08:00:00'
    >>> computed.count
    12
    >>> computed.all
    ['2014-01-01T08:00:00', '2014-01-03T08:00:00', '2014-01-07T08:00:00', '2014-01-09T08:00:00',
     '2014-01-13T08:00:00', '2014-01-15T08:00:00', '2014-01-17T08:00:00', '2014-01-21T08:00:00',
     '2014-01-23T08:00:00', '2014-01-27T08:00:00', '2014-01-29T08:00:00', '2014-01-31T08:00:00']
    
As a convenience, you can get a handle on a generator function that will iterate through the
entire set, as such:

    >>> result = rule.result()
    >>> next(result)
    '2014-01-01T08:00:00'
    >>> next(result)
    '2014-01-03T08:00:00'
    >>> [r for r in result]
    ['2014-01-07T08:00:00', '2014-01-09T08:00:00', '2014-01-13T08:00:00', '2014-01-15T08:00:00',
    '2014-01-17T08:00:00', '2014-01-21T08:00:00', '2014-01-23T08:00:00', '2014-01-27T08:00:00',
    '2014-01-29T08:00:00', '2014-01-31T08:00:00']

## Variations of the daily rule

You don't have to provide an end date - you can instead provide a number of occurrences
or in the lingo of `turoboro`: `repeat_n_times`. As such:

    >>> rule.repeat_n_times(10)
    # ValueError: You may not specify both an end date and a repeat count

Oops, lets first kill the end date, (because lets be explicit with our intentions.)
    
    >>> rule.end_on(None).repeat_n_times(100)
    {"end": null, "every_nth_day": 2, "except_days": [5, 6], "except_months": null, "on_hour": 8, "repeat": 100, "rule": "daily", "start": "2014-01-01T08:00:00+00:00", "timezone": "UTC"}
    
You can also let your rule be infinite by omitting to provide an end date or a number of 
occurrences. The `computed.first`, `computed.last` and `computed.all` attributes will still
behave as if the result is a bounded set (defaults to 100 occurrences). However, by
using the `rule.result()` generator function you can iterate forward beyond the bounds that
`rule.compute()` would give. Not infinitely far though, so iterating through the generator
will eventually come to a stop, how quickly depends on the batch size that you specify with
the keyword `max_count_if_infinite`. A `max_count_if_infinite=2` will likely give you results
several years into the future.

    >>> result = rule.result(max_count_if_infinite=2)
    >>> [r for r in result] # 1974 results
    
In essence - iterating through an infinite set of datetimes isn't very useful. Since, well...
they will never end. However, once you have an "infinite" rule you can always find the next
upcoming set of valid datetimes by simply telling `compute` or `result` and specify the
`from_dt` parameter, such as:

    >>> result = rule.result(from_dt=datetime.utcnow())
    >>> next(result)
    '2019-06-26T08:00:00'
