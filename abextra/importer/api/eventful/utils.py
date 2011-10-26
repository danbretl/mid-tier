import datetime
import dateutil.parser
import dateutil.rrule
import dateutil.relativedelta
import logging
from django.conf import settings
from core.parsers import datetime_parser
from core.parsers import price_parser

_LOGGER = logging.getLogger('importer.api.eventful.utils')

class temporal_parser():
    _FORMATS = ('%Y-%m-%d %H:%M:%S', '%Y%m%dT%H%M%S', '%Y-%m-%d%H:%M:%S')

    @classmethod
    def _parse_datetime(cls, dt_string):
        return datetime_parser.parse(dt_string, cls._FORMATS)

    @classmethod
    def _rdates(cls, dates_raw):
        dates_raw = dates_raw if isinstance(dates_raw, list) else [dates_raw]
        for date_raw in dates_raw:
            yield cls._parse_datetime(date_raw)

    @staticmethod
    def _rrules(rules_raw, dtstart):
        rules_raw = rules_raw if isinstance(rules_raw, list) else [rules_raw]
        for rule_raw in rules_raw:
            rule_raw = rule_raw.replace('BYDAY', 'BYWEEKDAY')
            yield dateutil.rrule.rrulestr(rule_raw, dtstart=dtstart, cache=True, compatible=True)

    @classmethod
    def _get_recurrence(cls, event_raw):
        rdates, rrules, exdates, exrules = set(), set(), set(), set()
        recurrence_raw = event_raw.get('recurrence')
        if recurrence_raw:
            # dtstart | original first instance
            instances_raw = recurrence_raw['instances']['instance']
            instances_raw = instances_raw if isinstance(instances_raw, list) else [instances_raw]
            first_instance_raw = instances_raw[0]       # assume presorted order
            dtstart = cls._parse_datetime(first_instance_raw['start_time'])
            # rdates, rrules
            rdates_raw, rrules_raw = map(recurrence_raw.get, ('rdates', 'rrules'))
            if rdates_raw:
                rdate_raw = rdates_raw.get('rdate')
                if rdate_raw:
                    rdates.update(cls._rdates(rdate_raw))
            if rrules_raw:
                rrule_raw = rrules_raw.get('rrule')
                if rrule_raw:
                    rrules.update(cls._rrules(rrule_raw, dtstart))
                    # exdates, exrules (exceptions)
            exdates_raw, exrules_raw = map(recurrence_raw.get, ('exdates', 'exrules'))
            if exdates_raw:
                exdate_raw = exdates_raw.get('exdate')
                if exdate_raw:
                    exdates.update(cls._rdates(exdate_raw))
            if exrules_raw:
                exrule_raw = exrules_raw.get('exrule')
                if exrule_raw:
                    exrules.update(cls._rrules(exrule_raw, dtstart))
        return rdates, rrules, exdates, exrules

    @classmethod
    def _recurrence_set(cls, event_raw, horizon=settings.IMPORT_EVENT_HORIZONS['eventful']):
        recurrences = set()
        start_time = cls._parse_datetime(event_raw['start_time'])
        rdates, rrules, exdates, exrules = cls._get_recurrence(event_raw)
        dtstop = start_time + horizon
        recurrences.update(rdates)
        for rrule in rrules:
            recurrences.update(rrule.between(start_time, dtstop, inc=True))
        recurrences.difference_update(exdates)
        for exrule in exrules:
            recurrences.difference_update(exrule.between(start_time, dtstop, inc=True))
        return recurrences

    @classmethod
    def _start_duration_allday(cls, event_raw):
        """Return event temporals."""
        start_time_raw, stop_time_raw, all_day_raw = map(event_raw.get,
            ('start_time', 'stop_time', 'all_day')
        )
        # coalesce datatypes
        start_datetime = cls._parse_datetime(start_time_raw)
        stop_datetime = cls._parse_datetime(stop_time_raw) if stop_time_raw else None
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

    @classmethod
    def occurrences(cls, event_raw):
        occurrences = set()
        start_datetime, duration, is_all_day = cls._start_duration_allday(event_raw)
        occurrences.add(start_datetime)
        occurrences.update(cls._recurrence_set(event_raw))
        return sorted(occurrences), duration, is_all_day


def expand_prices(data):
    raw_free = data.get('free')
    raw_price = data.get('price')
    prices = []
    # strange int check cause '1' or '0' comes back as a string
    if raw_free and int(raw_free):
        prices = [0.00]
    elif raw_price:
        parsed_prices = price_parser.parse(raw_price)
        # discard duplicates and instances of 0.00 if not set to free
        if parsed_prices:
            prices = set(parsed_prices)
            prices.discard(0)
        else:
            _LOGGER.warn('Unable to parse prices from %s' % raw_price)
    else:
        _LOGGER.warn('"Free" nor "Price" fields could not be found.')
    return map(lambda price: dict(quantity=str(price)), sorted(list(prices)))



