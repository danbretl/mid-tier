import logging
from itertools import count, chain
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

class FeedIntegrityError(Exception): pass
    # def __init__(self, *args, item_guid, **kwargs):

class ScrapeFeedConsumer(object):
    """
    Consumer reads the feed file one line at time.  Every line is a json
    of a scraped item (Category, Event, Occurrence, or Location).
        events() will also produce a generator of fully-related events.
    """
    registry = {}
    logger = logging.getLogger('consumer.scrape')

    def __init__(self, feed_path=None, do_cleanup=True):
        feed_reader = ScrapeFeedReader(feed_path)
        self.do_cleanup = do_cleanup

        # register (add) all items to the registry
        for item in feed_reader.read():
            self._register(item)

        # relate all items
        self._wire_all()

    def items(self, item_type, source=None):
        source_regs = (self.registry[source],) if source \
            else self.registry.itervalues()
        gen_it_list = []
        for source_reg in source_regs:
            try:
                gen_it_list.append(source_reg[item_type].itervalues())
            except KeyError:
                pass
        return chain(*gen_it_list)

        # return chain(
        #     *(source_reg[item_type].itervalues() for source_reg in source_regs)
        #     )

    def categories(self, source=None):
        return self.items('category', source)

    def prices(self, source=None):
        return self.items('price', source)

    def events(self, source=None):
        return self.items('event', source)

    def occurrences(self, source=None):
        return self.items('occurrence', source)

    def locations(self, source=None):
        return self.items('location', source)

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
        l = lambda item_type: self.registry[item_source].get(item_type, {})
        categories, events, prices, occurrences, locations = \
            map(l, ('category', 'event', 'price', 'occurrence', 'location'))

        # FIXME hacked in until proper M2M M2ONE ONE2M relaters
        prices_by_occurrence_guid = {}
        for guid, price in prices.iteritems():
            # Adding a try-except
            # Handle the case where a scrape may not have occurrence_guids
            try:
                prices_by_occurrence_guid.setdefault(price.occurrence_guid, [])\
                                                                  .append(price)
            except:
                #FIXME: log an error message
                pass

        for guid, occurrence in occurrences.items():
            try:
                # location to occurrence    (one to many)
                location_guid = occurrence.get('location_guid')
                location = locations.get(location_guid)
                if not location:
                    if self.do_cleanup: del occurrences[guid]
                    raise FeedIntegrityError('failed to relate: Occurrence to Location | occurrence_guid: %s\tlocation_guid: %s' % (str(guid), str(location_guid)))
                occurrence['location'] = location

                # prices to occurrence  (many to one)
                occurrence['prices'] = prices_by_occurrence_guid \
                    .get(occurrence.guid, [])

                # occurrence to event (many to one)
                event_guid = occurrence.get('event_guid')
                event = events.get(event_guid)
                if not event:
                    if self.do_cleanup: del occurrences[guid]
                    raise FeedIntegrityError('failed to relate: Occurrence to Event | occurrence_guid: %s\tevent_guid: %s' % (guid.encode('unicode_escape'), event_guid.encode('unicode_escape')))
                event.setdefault('occurrences', []).append(occurrence)

                # categories to event (many to one)
                category_guids = event.get('category_guids')
                if category_guids:
                    for category_guid in category_guids:
                        category = categories.get(category_guid)
                        if category:
                            event.setdefault('categories', []).append(category)

            except FeedIntegrityError as error:
                self.logger.warn(error)

        if self.do_cleanup:
            for guid, event in events.items():
                if not event.get('occurrences'):
                    del events[guid]
                    self.logger.warn('Removing an Event with no occurrences | guid: %s' % guid)
