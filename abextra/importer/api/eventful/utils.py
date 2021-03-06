import dateutil.parser
import dateutil.rrule
import dateutil.relativedelta
import logging
from core.parsers import datetime_parser

_LOGGER = logging.getLogger('importer.api.eventful.utils')

class temporal_parser():
    _FORMATS = ('%Y-%m-%d %H:%M:%S', '%Y%m%dT%H%M%S', '%Y-%m-%d%H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y%m%dT%H:%M:%S')

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
            rule_raw = rule_raw.replace('BYDAY', 'BYWEEKDAY').strip(' ;')
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
    def _recurrence_set(cls, event_raw):
        recurrences = set()
        start_time = cls._parse_datetime(event_raw['start_time'])
        kwiqet_data = event_raw['__kwiqet']
        horizon_stop = kwiqet_data['horizon_stop']
        rdates, rrules, exdates, exrules = cls._get_recurrence(event_raw)
        rdates_clipped = (rdate for rdate in rdates if rdate >= start_time and rdate <= horizon_stop)
        recurrences.update(rdates_clipped)
        for rrule in rrules:
            recurrences.update(rrule.between(start_time, horizon_stop, inc=True))
        recurrences.difference_update(exdates)
        for exrule in exrules:
            recurrences.difference_update(exrule.between(start_time, horizon_stop, inc=True))
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
        all_day = int(all_day_raw) if all_day_raw else 2
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
