import eventful_api.eventful_api as eventful
import logging
import itertools
from django.conf import settings
import events.models

class EventfulImporter(object):


    def __init__(self,events_per_page=100, query='', location='New York City'):
        self.logger = logging.getLogger('importer.eventful_import')
        self.count = 0
        self.api = eventful.API(settings.EVENTFUL_API_KEY)
        self.events = []
        self.events_per_page = events_per_page 
        self.query = query
        self.location = location
        self.total_items = 0
        self.current_page = 1

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

    def import_events(self, ):
        # api call to get metadata
        metadata = self.api.call('/events/search/',
                q=self.query,l=self.location, page_size=100)
        self.total_items = int(metadata['total_items'])
        page_count = int(metadata['page_count'])

        self.logger.info('Found %d current events in %s' %
                (self.total_items, self.location))
        self.logger.info('Fetching %d pages (%d events per page) ...' %
                (page_count, self.events_per_page))
        self.logger.info('Starting from page %d/%d' %
                (self.current_page, page_count))

        for ix_page in range(self.current_page, page_count + 1):
            self.current_page = ix_page
            for event in self.import_page(ix_page):
                # import ipdb; ipdb.set_trace()
                event = self.process_event(event)
                self.events.append(event)
            self.logger.info('Fetched %d/%d events so far' %
                    (self.count, self.total_items))

    # FIXME: implement JSON dump events & settings
    def json_dump():
        pass

    # FIXME: implement JSON load events & settings
    def json_load():
        pass

    def import_page(self, page_number):
        page = self.api.call('/events/search', q=self.query,
                l=self.location, page_size=self.events_per_page,
                page_number=page_number)
        # import ipdb; ipdb.set_trace()
        self.logger.info('Fetched page %d in %f s' % (page_number,
                float(page['search_time'])))
        # import ipdb; ipdb.set_trace()
        return page['events']['event']

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
