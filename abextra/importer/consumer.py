import logging
from itertools import ifilter
from django.utils import simplejson
from django.conf import settings
from core.utils import Bunch

class ScrapeFeedReader(object):
    def __init__(self, path=None):
        self.path = path or settings.SCRAPE_FEED_PATH

    def read(self):
        with open(self.path) as feed:
            for jsonline in feed:
                yield Bunch(simplejson.loads(jsonline))

class ScrapeFeedConsumer(object):
    """
    Consumer reads the feed file one line at time.  Every line is a json
    of a scraped item (Category, Event, Occurrence, or Location).
        events() will also produce a generator of fully-related events.
    """
    registry = {}
    logger = logging.getLogger('consumer.scrape')

    def __init__(self, feed_path=None):
        feed_reader = ScrapeFeedReader(feed_path)
        # register (add) all items to the registry
        for item in feed_reader.read():
            self._register(item)
        # relate all items
        self._wire_all()

    def _items(self, item_type):
        for source_registry in self.registry.itervalues():
            for item in source_registry[item_type].itervalues():
                yield item

    @property
    def categories(self):
        return self._items('category')

    @property
    def prices(self):
        return self._items('price')

    @property
    def events(self, filter_incomplete=True):
        events = self._items('event')
        if not filter_incomplete:
            return events
        return ifilter(lambda e: e.get('occurrences'), events)

    @property
    def occurrences(self):
        return self._items('occurrence')

    @property
    def locations(self):
        return self._items('location')

    def _register(self, item):
        item_source = item.get('source')
        if item_source:
            source_registry = self.registry.setdefault(item_source, {})

        item_type = item.get('type')
        if item_type:
            type_registry = source_registry.setdefault(item_type, {})

        item_guid = item.get('guid')
        if item_guid:
            type_registry[item_guid] = item

    def _wire_all(self):
        for item_source in self.registry.iterkeys():
            self._wire_source(item_source)

    def _wire_source(self, item_source):
        l = lambda item_type: self.registry[item_source][item_type]
        categories, events, prices, occurrences, locations = \
            map(l, ('category', 'event', 'price', 'occurrence', 'location'))

        # FIXME hacked in until proper M2M M2ONE ONE2M relaters
        prices_by_occurrence_guid = {}
        for guid, price in prices.iteritems():
            prices_by_occurrence_guid.setdefault(price.occurrence_guid, []) \
                .append(price)

        # The goal is to wire up as much as we can ignoring any errors.
        # The minimum requirements include:
        # a) Each occurrence must have a corresponding event, else ignore.
        # b) Each occurrence must have a location, else ignore.
        # c) Each occurrence may have categories.
        #    - This is a questionable design. Will leave for discussion later.
        for guid, occurrence in occurrences.iteritems():

            # location to occurrence    (one to many)
            location_guid = occurrence.get('location_guid')
            location = locations.get(location_guid)
            if not location:
                self.logger.warn('failed to relate: Occurrence: '
                                 + occurrence.get('event_guid')
                                 + ' to Event')
                continue

            occurrence['location'] = location

            # prices to occurrence  (many to one)
            occurrence['prices'] = prices_by_occurrence_guid \
                .get(occurrence.guid, [])

            # occurrence to event (many to one)
            event_guid = occurrence.get('event_guid')
            event = events.get(event_guid)
            if not event:
                # This means we have an occurrence with no corresponding event.
                self.logger.warn('failed to relate: Occurrence: ' \
                                  + occurrence.get('event_guid')
                                 + ' to Event')
                continue
            event.setdefault('occurrences', []).append(occurrence)

            # categories to event (many to one)
            category_guids = event.get('category_guids')
            if category_guids:
                for category_guid in category_guids:
                    category = categories.get(category_guid)
                    if category:
                        event.setdefault('categories', []).append(category)
