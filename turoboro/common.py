from datetime import datetime, timedelta, tzinfo
import turoboro
import calendar


def is_iso_datetime(iso_timestamp):
    return iso_timestamp if datetime.strptime(iso_timestamp[0:19], '%Y-%m-%dT%H:%M:%S') else None


def is_list_of_days(days):
    if not isinstance(days, (list, tuple)):
        raise ValueError('Expecting a list or tuple of days of the week, each "day" being an int between 0 to 6')

    invalid_days = [d for d in days if d not in turoboro.DAYS]

    if invalid_days:
        raise ValueError('Expecting a valid days of the week, between 0 and 6. Invalids %s' % invalid_days)

    if len(days) > 7:
        raise ValueError('There are only seven days to a week, not %s' % len(days))

    return days


def is_list_of_months(months):
    if not isinstance(months, (list, tuple)):
        raise ValueError('Expecting a list or tuple of months of the year, each "month" being an int between 1 to 12')

    invalid_months = [m for m in months if m not in turoboro.MONTHS]

    if invalid_months:
        raise ValueError('Expecting valid months of the year, between 1 to 12. Invalid: %s' % invalid_months)

    if len(months) > 12:
        raise ValueError('There are only twelve months to a year, not %s' % len(months))

    return months


def datetime_from_isoformat(ts):
    return datetime.strptime(ts[:19], '%Y-%m-%dT%H:%M:%S')


def convert_datetime_to(dt, to=turoboro.ISO):
    if to == turoboro.ISO:
        return dt.isoformat()
    if to == turoboro.POSIX:
        return int(calendar.timegm(dt.timetuple()))

    return dt
