import datetime
import dateutil.parser
import dateutil.rrule
import dateutil.relativedelta
import logging
from django.conf import settings

_LOGGER = logging.getLogger('importer.api.eventful.utils')

def expand_rrules(rrule_strings, first_occurrence, lower_bound, upper_bound):
    occurrences = set()
    for rrule_string in rrule_strings:
        rrule_cleaned = rrule_string.replace('BYDAY', 'BYWEEKDAY')
        rrule = dateutil.rrule.rrulestr(rrule_cleaned, dtstart=first_occurrence)
        rrules_bound = rrule.between(lower_bound, upper_bound)
        occurrences = occurrences.union(rrules_bound)
    return occurrences

# FIXME dead code unless Eventful API to return dates in different format
def parse_temporal(datetime_str):
    """Eventful often returns a null date string and time string which has
    both date and time, so let's try parsing that into first_occurrence.
    """
    parse_dt = lambda f: datetime.datetime.strptime(datetime_str, f)
    parsed_temporal = None
    try:
        parsed_temporal = parse_dt('%Y-%m-%d %H:%M:%S')
    except ValueError:
        try:
            parsed_temporal = parse_dt('%Y%m%dT%H%M%S')
        except ValueError:
            # Couldn't parse date and time, try just date
            try:
                parsed_temporal = parse_dt('%Y-%m-%d').date()
            except ValueError:
                # Couldn't parse date+time nor date, try just time
                try:
                    parsed_temporal = parse_dt('%H:%M:%S').time()
                except ValueError:
                    _LOGGER.debug('Unable to parse datetime nor date nor time from: %s' % datetime_str)
    return parsed_temporal


def expand_recurrence_dict(recurrence_dict, start_datetime, lower_bound=datetime.datetime.now()):
    start_datetimes = set()
    first_occurrence = start_datetime

    # some events are returned by the api with start_datetimes in the past because
    # because their durations are erroneously wayyy to long
    if start_datetime > lower_bound:
        start_datetimes.add(start_datetime)

    # determine the upper bound | import horizon from the start date
    upper_bound = start_datetime + settings.IMPORT_EVENT_HORIZONS['eventful']

    # add rdates to recurrence set
    rdates_field = recurrence_dict.get('rdates')
    if rdates_field:
        rdates_raw = rdates_field.get('rdate')
        if rdates_raw:
            # coerce into a list
            rdates_raw = rdates_raw if isinstance(rdates_raw, list) else [rdates_raw]
            # parse temporals
            rtemporals = (parse_temporal(rdate_raw) for rdate_raw in rdates_raw)
            # pick datetimes
            rdatetimes = sorted(rtemporal for rtemporal in rtemporals if isinstance(rtemporal, datetime.datetime))
            
            for rdatetime in rdatetimes:
                rtemporal = parse_temporal(rdate)
                if isinstance(rtemporal, datetime.datetime) and rtemporal > lower_bound:
                    if rtemporal > lower_bound:
                        start_datetimes.add(rtemporal)

    # add rrules to recurrence set
    if rrules:
        rrule_raw = rrules.get('rrule')
        if rrule_raw:
            # convert field to a list
            rrule_strings = rrule_raw if isinstance(rrule_raw, list) else [rrule_raw]
            rrules = expand_rrules(rrule_strings, start_datetime)
            start_datetimes = start_datetimes.union(rrules)

    # clip set to take out times in the past, then parse
    current_date_times = filter(lambda x: x > lower_bound and x < upper_bound, start_datetimes)

    # we want to return the first occurrence for verification purposes --
    # this could make it easier to validate correct behavior parsing rdates
    # in a unit test

    return start_date, current_date_times


def parse_start_datetime_and_duration(raw_data):
    start_time_raw, stop_time_raw = map(raw_data.get, ('start_time', 'stop_time'))

    start_temporal = parse_temporal(start_time_raw)
    stop_temporal = parse_temporal(stop_time_raw)

    start_datetime, duration = None, None
    if isinstance(start_temporal, datetime.datetime):
        start_datetime = start_temporal
        if isinstance(stop_temporal, datetime.datetime):
            duration = start_datetime - start_temporal

    return start_datetime, duration


def expand_occurrences(raw_data):
    # always expect to parse a start datetime, but not necessarily duration
    start_datetime, duration = parse_start_datetime_and_duration(raw_data)
    if not start_datetime:
        raise ValueError('Could not parse start datetime')
    recurrence_dict = raw_data.get('recurrence')
    if recurrence_dict:
        first_occurrence, current_date_times = expand_recurrence_dict(recurrence_dict, start_datetime)
        for date_time in current_date_times:
            occurrence_form_dicts.append(prepare_occurrence(raw_data, date_time, duration))
    return occurrence_form_dicts


def expand_prices(data, quantity_parser):
    raw_free = data.get('free')
    raw_price = data.get('price')
    # strange int check cause '1' or '0' comes back as a string
    if raw_free and int(raw_free):
        prices = [0.00]
    elif raw_price:
        prices = quantity_parser.parse(raw_price)
    else:
        prices = []
        _LOGGER.warn('"Free" nor "Price" fields could not be found.')
    return map(lambda price: dict(quantity=str(price)), prices)

def current_event_horizon():
    """
    Calculates date range string for eventful query based on current date and
    event horizon specified in settings.
    """
    current_date = datetime.datetime.now().date()
    end_date = datetime.datetime.now().date() + settings.IMPORT_EVENT_HORIZONS['eventful']
    date_range_string = '%s00-%s00' % (current_date.isoformat().replace('-',''),
            end_date.isoformat().replace('-',''))
    return date_range_string 
