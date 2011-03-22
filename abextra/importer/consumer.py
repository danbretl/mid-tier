from django.utils import simplejson
from django.conf import settings

class ScrapeFeedConsumer(object):
    """
    Consumer reads the feed file one line at time.  Every line is a json
    of a scraped item (Category, Event, Occurrence, or Location).
        events() will also produce a generator of fully-related events.
    """
    registry = {}

    def __init__(self):
        for item in self._read_feed():
            self._register(item)

    def events(self):
        self._wire_all()
        for source_registry in self.registry.itervalues():
            for event in source_registry['event'].itervalues():
                yield event

    def _read_feed(self):
        with open(settings.SCRAPE_FEED_PATH) as feed:
            for jsonline in feed:
                yield simplejson.loads(jsonline)

    def _register(self, item):
        item_source = item['source']
        source_registry = self.registry.setdefault(item_source, {})

        item_type = item['type']
        source_type_registry = source_registry.setdefault(item_type, {})

        item_guid = item['guid']
        source_type_registry[item_guid] = item

    def _wire_all(self):
        for item_source in self.registry.iterkeys():
            self._wire_source(item_source)

    def _wire_source(self, item_source):
        l = lambda item_type: self.registry[item_source][item_type]
        guid_category, guid_event, guid_occurrence, guid_location = \
            map(l, ('category', 'event', 'occurrence', 'location'))

        for guid, occurrence in guid_occurrence.iteritems():
            location_guid = occurrence['location_guid']
            location = guid_location[location_guid]
            occurrence['location'] = location

            event_guid = occurrence['event_guid']
            event = guid_event[event_guid]
            event.setdefault('occurrences', []).append(occurrence)

            category_guids = event['category_guids']
            for category_guid in category_guids:
                category = guid_category[category_guid]
                event.setdefault('categories', []).append(category)
