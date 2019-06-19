# turoboro
A python library for specifying time rules and getting sensible timestamps in return.

I.e this library answers the question: when is the next time this happens?

Say for example you want to find out at what specific UTC time the rule "every thursday of every
third week of every second month at 8 o'clock UTC" would happen.

Ask turoboro! 


## Usage

Lets assume today is Tuesday June 18th, 2019. Here are the repercussions of using the `turoboro.Rule`
class to generate timestamps for when the rule should trigger into the future.

### Daily

Example: "Every day at 8 o'clock, except on weekends, and never in June."

    >>> import turoboro
    >>> rule = turoboro.DailyRule()
    >>> rule.repeat_every(3)
    >>> rule.except_week_days((turoboro.SATURDAY,turoboro.SUNDAY))
    >>> rule.except_months((turoboro.JUNE,))
    >>> rule.compute()
    
    >>> rule.get_spec()
    {
        "start": "2019-06-18T21:19:57",
        "end": None
        "rule": "daily",
        "repeat": 3,
        "exceptWeekdays": [0,6],
        "exceptMonths": [6],
        "hour": 0  # Default to hour 0 if unspecified
    }
    