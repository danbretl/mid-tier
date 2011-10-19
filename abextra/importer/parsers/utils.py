import re
import os
import datetime
import HTMLParser
import dateutil.parser
import dateutil.rrule
from django.conf import settings

def expand_rrules(first_occ, rrule_strings):
    rrules = set()
    for rrule_string in rrule_strings:
        rrule_cleaned = rrule_string.replace('BYDAY', 'BYWEEKDAY')
        rrule = dateutil.rrule.rrulestr(rrule_cleaned)
        last_occ = first_occ + dateutil.relativedelta.relativedelta(**settings.EVENTFUL_RRULE_MAX)
        rrules_clipped = rrule.between(first_occ, last_occ)
        rrules.union(rrules_clipped)
    return rrules

def parse_datetime_or_date_or_time(datetime_str):
    parsed_datetime, parsed_date, parsed_time = None, None, None
    if datetime_str:
        try:
            parsed_datetime = datetime.datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            # Couldn't parse date and time, try just date
            try:
                parsed_date = datetime.datetime.strptime(datetime_str, '%Y-%m-%d')
            except ValueError:
                # Couldn't parse date+time or date, try just time
                try:
                    parsed_time = datetime.datetime.strptime(datetime_str, '%H:%M:%S')
                except ValueError:
                    print('Unable to parse datetime string <%s>' %
                            datetime_str)
    return (parsed_datetime, parsed_date, parsed_time)

def expand_recurrence_dict(recurrence_dict, first_occ, clip_before=datetime.datetime.now()):
    rdates, rrules = map(recurrence_dict.get, ('rdates', 'rrules'))
    # make initial set of date_times from start_time
    date_times = set([first_occ])
    last_occ = first_occ + dateutil.relativedelta.relativedelta(**settings.EVENTFUL_RRULE_MAX)

    # add rdates to set of recurrences

    if rdates:
        rdate_field = rdates.get('rdate')
        if rdate_field:
            rdate_field = [rdate_field] if not isinstance(rdate_field, (tuple, list)) else rdate_field
            if len(rdate_field) > 0:
                try:
                    first_occ = dateutil.parser.parse(rdate_field[0])
                except:
                    print('%Error parsing date from rdate string <%s>')
            for rdate in rdate_field:
                try:
                    # dateutil sometimes parses on malformed rdate
                    # strings from eventful
                    date_times.add(dateutil.parser.parse(rdate))
                except ValueError:
                    print('Unable to parse date from rdate field: <%s>' % rdate)

    # add rrules to set of recurrences

    if rrules:
        rrule_field = rrules.get('rrule')
        if rrule_field:
            # convert field to a list
            rrule_strings = rrule_field if isinstance(rrule_field, (list, tuple)) else [rrule_field]
            rrules = expand_rrules(first_occ, rrule_strings)
            date_times.union(rrules)

    # clip set to take out times in the past, then parse
    current_date_times = filter(lambda x: x > clip_before and x < last_occ, date_times)

    # we want to return the first occurrence for verification purposes --
    # this could make it easier to validate correct behavior parsing rdates
    # in a unit test

    return (first_occ, current_date_times)

def parse_start_datetime_and_duration(data):
    start_time_field = data.get('start_time')
    stop_time_field = data.get('stop_time')

    # Eventful often returns a null date string and time string which has
    # both date and time, so let's try parsing that into first_occ

    (start_date_and_time, start_date_only, start_time_only) = parse_datetime_or_date_or_time(start_time_field)
    (end_date_and_time, end_date_only, end_time_only) = parse_datetime_or_date_or_time(stop_time_field)

    # After this point, we need to check if only end_time_only was emitted --
    # in this case, if start_date_and_time exists, then we can still do a
    # successful parse, but we want to use dateutil to parse the datetime
    # field again: this is because dateutil allows one to pass a default
    # datetime string if fields are missing, so we can pass in the
    # successfully parsed start_date_and_time.

    if start_date_and_time and end_time_only and not end_date_and_time:
        end_time_only = dateutil.parser.parse(stop_time_field,
                default=start_date_and_time)

    # Only bother adding occurrence if it has starting date or date+time
    # If occurrence has end date then calculate duration and apply to each
    # recurrence
    # FIXME: check if it's all day, and handle that for recurrence cases

    if start_date_and_time or start_date_only:
        start_datetime = start_date_and_time or start_date_only

        # NOTE: here, I am making the assumption that an event without an
        # express end time should not be parsed as if it has duration

        if start_date_and_time and (end_date_and_time or end_time_only):
            end_time = end_date_and_time or end_time_only
            duration = end_time - start_date_and_time
        else:
            duration = None

    return (start_datetime, duration)

def prepare_occurrence(data, start_datetime, duration):
    occurrence_form_data = data
    occurrence_form_data['start_date'] = \
        start_datetime.date().isoformat()
    occurrence_form_data['start_time'] = \
        start_datetime.time().isoformat()
    if duration:
        end_datetime = start_datetime + duration
        occurrence_form_data['end_date'] = \
            end_datetime.date().isoformat()
        occurrence_form_data['end_time'] = \
            end_datetime.time().isoformat()
    return occurrence_form_data

def expand_occurrences(data):
    (start_datetime, duration) = parse_start_datetime_and_duration(data)
    recurrence_dict = data.get('recurrence')
    occurrence_form_dicts = []
    if recurrence_dict:
        (first_recurrence, current_date_times) = expand_recurrence_dict(recurrence_dict, start_datetime)
        for date_time in current_date_times:
            occurrence_form_dicts.append(prepare_occurrence(data, date_time, duration))
    return occurrence_form_dicts


