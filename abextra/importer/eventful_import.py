import logging
import itertools
import eventful
from django.conf import settings
from importer.parsers.eventful import EventfulEventParser
from importer.eventful_api.loader import SimpleApiConsumer
import events.models

class EventfulImporter(object):

    def __init__(self, current_page=1, page_size=100, query='', location='NYC'):
        self.consumer = SimpleApiConsumer(api_key=settings.EVENTFUL_API_KEY)
        self.parser = EventfulEventParser()
        self.logger = logging.getLogger('importer.eventful_import')
        self.count = 0
        self.api = eventful.API(settings.EVENTFUL_API_KEY)
        self.events = []
        self.page_size = page_size 
        self.query = query
        self.location = location
        self.total_items = 0
        self.current_page = current_page 

    # custom __getstate__ and __setstate__ for pickling and unpickling

    def __getstate__(self):
        result = self.__dict__.copy()
        result['api'] = settings.EVENTFUL_API_KEY
        del result['logger']
        return result

    def __setstate__(self, dict):
        self.__dict__ = dict
        self.api = eventful.API(settings.EVENTFUL_API_KEY)
        self.logger = logging.getLogger('importer.eventful_import')

    def import_events(self, total_pages=0):
        # api call to get metadata
        metadata = self.api.call('/events/search/',
                q=self.query,l=self.location,
                page_size=self.page_size)
        self.total_items = int(metadata['total_items'])
        page_count = int(metadata['page_count'])

        # set last page in range to be fetched
        if not total_pages:
            last_page = page_count + 1
        else:
            last_page = self.current_page + total_pages
            if last_page > page_count + 1:
                last_page = page_count + 1

        self.logger.info('Found %d current events in %s' %
                (self.total_items, self.location))
        self.logger.info('Fetching %d pages (%d events per page) ...' %
                (page_count, self.page_size))
        self.logger.info('Starting from page %d/%d' %
                (self.current_page, page_count))

        for ix_page in range(self.current_page, last_page):
            self.current_page = ix_page
            events = self.consumer.consume(location=self.location, date='Today',
                page_size=self.page_size, page_number=self.current_page)
            for event in events:
                # try:
                self.process_event(event)
                event_obj = self.parser.parse(event)
                # THIS IS VERY UGLY
                # FIXME
                # HANDLE THA DAMN EXCEPTIONS
                # except Exception as e:
                    # raise e
                    # self.logger.warn("Encountered %s exception while parsing" %
                            # type(exception))
             
            self.logger.info('Fetched %d/%d events so far' %
                    (self.count, self.total_items))

    # FIXME: implement JSON dump events & settings
    def json_dump():
        pass

    # FIXME: implement JSON load events & settings
    def json_load():
        pass

    def process_event(self, e):
        # preprocess event response
        # convert to native objects
        # FIXME: use django forms to import
        # e = events.models.Event(xid=e['id'],
                # description=e['description'], url=e['url'],
                # created=e['created'], title=e['title'])
        # self.logger.info('Processing event %s' % e['title'])
        self.count += 1
        return e
        # pass
