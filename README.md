[![CircleCI](https://circleci.com/gh/pellepim/turoboro.svg?style=shield)](https://circleci.com/gh/pellepim/turoboro)
![Alt text](coverage.svg "Code coverage")
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

## Daily rule with an end date

    >>> import turoboro
    >>> from datetime import datetime
    >>> rule = turoboro.DailyRule(start=datetime(2014, 1, 1))
    >>> rule.every_nth_day(2)
    >>> rule..except_weekdays(*turoboro.WEEKEND)
    >>> rule.end_on(datetime(2014, 1, 31))
    >>> rule.on_hour(8)
    
Alright, now we have an instance of the `DailyRule` class - starting January 1st 2014 and ending
January 31st 2014, set to occur every second day at 8 AM - except on week-ends.

You can also instantiate the exact same thing using only a constructor:

    >>> rule = turoboro.DailyRule(
    ...     datetime(2014, 1, 1), every_nth_day=2, except_weekdays=turoboro.WEEKEND,
    ...     end_on=datetime(2014, 1, 31), on_hour=8
    ... )

Lets see what actual times this resolves to.

    >>> result = rule.compute()
    >>> result.first
    '2014-01-01T08:00:00'
    >>> result.last
    '2014-01-31T08:00:00'
    >>> result.count
    12
    >>> result.all
    ['2014-01-01T08:00:00', '2014-01-03T08:00:00', '2014-01-07T08:00:00', '2014-01-09T08:00:00',
     '2014-01-13T08:00:00', '2014-01-15T08:00:00', '2014-01-17T08:00:00', '2014-01-21T08:00:00',
     '2014-01-23T08:00:00', '2014-01-27T08:00:00', '2014-01-29T08:00:00', '2014-01-31T08:00:00']
    
