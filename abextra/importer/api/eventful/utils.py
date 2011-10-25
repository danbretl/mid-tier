import datetime
import dateutil.parser
import dateutil.rrule
import dateutil.relativedelta
import logging
from django.conf import settings
from core.parsers import datetime_parser

_LOGGER = logging.getLogger('importer.api.eventful.utils')

class temporal_parser():
    _FORMATS = ('%Y-%m-%d %H:%M:%S', '%Y%m%dT%H%M%S', '%Y-%m-%d%H:%M:%S')

    @classmethod
    def parse_datetime(cls, dt_string):
        return datetime_parser.parse(dt_string, cls._FORMATS)

    @classmethod
    def _get_dates(cls, dates_raw):
        dates_raw = dates_raw if isinstance(dates_raw, list) else [dates_raw]
        return set(cls.parse_datetime(date_raw) for date_raw in dates_raw)

    @staticmethod
    def _get_rules(rules_raw, dtstart):
        rules_raw = rules_raw if isinstance(rules_raw, list) else [rules_raw]
        rules = set()
        for rule_raw in rules_raw:
            rule_raw = rule_raw.replace('BYDAY', 'BYWEEKDAY')
            rule = dateutil.rrule.rrulestr(rule_raw, dtstart=dtstart,
                                           cache=True, compatible=True)
            rules.add(rule)
        return rules

    @classmethod
    def _get_recurrence(cls, event_raw, start_time):
        rdates, rrules, exdates, exrules = set(), set(), set(), set()
        recurrence_raw = event_raw.get('recurrence')
        if recurrence_raw:
            # dtstart | original first instance or start_time
            dtstart = start_time
            instances_raw = recurrence_raw.get('instances')
            if instances_raw:
                instance_raw = instances_raw.get('instance')
                if instance_raw:
                    instance_raw = instance_raw if isinstance(instance_raw, list) else [instance_raw]
                    # rely on sorted order from API
                    first_instance_raw = instance_raw[0]
                    dtstart = cls.parse_datetime(first_instance_raw['start_time'])
                    # rdates, rrules
            rdates_raw, rrules_raw = map(recurrence_raw.get, ('rdates', 'rrules'))
            if rdates_raw:
                rdate_raw = rdates_raw.get('rdate')
                if rdate_raw:
                    rdates.update(cls._get_dates(rdate_raw))
            if rrules_raw:
                rrule_raw = rrules_raw.get('rrule')
                if rrule_raw:
                    rrules.update(cls._get_rules(rrule_raw, dtstart))
                    # exdates, exrules (exceptions)
            exdates_raw, exrules_raw = map(recurrence_raw.get, ('exdates', 'exrules'))
            if exdates_raw:
                exdate_raw = rdates_raw.get('exdate')
                if exdate_raw:
                    exdates.update(cls._get_dates(exdate_raw))
            if exrules_raw:
                exrule_raw = exrules_raw.get('rrule')
                if exrule_raw:
                    exrules.update(cls._get_rules(exrule_raw, dtstart))
        return rdates, rrules, exdates, exrules

    @classmethod
    def recurrence_set(cls, event_raw, horizon=settings.IMPORT_EVENT_HORIZONS['eventful']):
        recurrences = set()
        start_time = cls.parse_datetime(event_raw['start_time'])
        rdates, rrules, exdates, exrules = cls._get_recurrence(event_raw, start_time)
        dtstop = start_time + horizon
        recurrences.update(rdates)
        for rrule in rrules:
            recurrences.update(rrule.between(start_time, dtstop, inc=True))
        recurrences.difference_update(exdates)
        for exrule in exrules:
            recurrences.difference_update(exrule.between(start_time, dtstop, inc=True))
        return recurrences

    @classmethod
    def start_duration_allday(cls, event_raw):
        """Return event temporals."""
        start_time_raw, stop_time_raw, all_day_raw = map(event_raw.get,
            ('start_time', 'stop_time', 'all_day')
        )
        # coalesce datatypes
        start_datetime = cls.parse_datetime(start_time_raw)
        stop_datetime = cls.parse_datetime(stop_time_raw) if stop_time_raw else None
        all_day = int(all_day_raw)
        # initialize outputs
        duration = stop_datetime - start_datetime if stop_datetime else None
        is_all_day = None
        # 0 => not all day, use time; 1 => all day, ignore time; 2 => unknown
        if all_day == 0:
            is_all_day = False
        elif all_day == 1:
            is_all_day = True
        return start_datetime, duration, is_all_day


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
    date_range_string = '%s00-%s00' % (current_date.isoformat().replace('-', ''),
                                       end_date.isoformat().replace('-', ''))
    return date_range_string 
