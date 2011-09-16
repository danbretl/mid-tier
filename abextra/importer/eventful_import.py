import eventful 
import progressbar
import logging
import itertools
from django.conf import settings


class EventfulImporter(object):

    def __init__(self,events_per_page=100, query='', location='New York City'):
        self.logger = logging.getLogger('importer.eventful_import')
        self.progress_bar = progressbar.ProgressBar()
        self.count = 0
        self.api = eventful.API(settings.EVENTFUL_API_KEY)
        self.events = []
        self.events_per_page = events_per_page 
        self.query = query
        self.location = location

    def import_events(self, ):
        # call w/ small page size to get metadata
        metadata = self.api.call('/events/search/',
                q=self.query,l=self.location, page_size=100)
        total_items = int(metadata['total_items'])
        page_count = int(metadata['page_count'])

        self.progress_bar.maxval=total_items
        self.logger.info('Found %d current events in %s' %
                (total_items, self.location))
        self.logger.info('Fetching %d pages (%d events per page) ...' %
                (page_count, self.events_per_page))

        self.progress_bar.start()
        for ix_page in range(1, page_count+ 1):
            for event in self.import_page(ix_page):
                # import ipdb; ipdb.set_trace()
                self.process_event(event)
        self.progress_bar.finish()

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
        # update progress bar
        print 'Processing event %s' % e['title']
        self.count += 1
        self.progress_bar.update(self.count)
        return e
        # pass 
