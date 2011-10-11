import logging
import itertools
from django.conf import settings
from importer.parsers.eventful import EventfulEventParser
from importer.eventful_api.loader import EventfulApiConsumer
import events.models

class EventfulImporter(object):

    def __init__(self, current_page=1, page_size=100, query='', location='NYC', mock_api=False, interactive=False, make_dumps=False):
        self.consumer = EventfulApiConsumer(api_key=settings.EVENTFUL_API_KEY, mock_api=mock_api, make_dumps=make_dumps)
        self.parser = EventfulEventParser()
        self.logger = logging.getLogger('importer.eventful_import')
        self.count = 0
        self.events = []
        self.page_size = page_size
        self.query = query
        self.location = location
        self.current_page = current_page
        self.interactive = interactive

    def import_events(self, total_pages=0):

        last_page = self.page_size + 1
        fetched_meta = False

        self.logger.info('Beginning import of eventful events...') 

        while self.current_page < last_page:
            events = self.consumer.consume(location=self.location, date='Today',
                page_size=self.page_size, page_number=self.current_page)

            if not fetched_meta:
                if not total_pages:
                    last_page = self.consumer.page_count + 1
                else:
                    last_page = self.current_page + total_pages
                    if last_page > self.consumer.page_count + 1:
                        last_page = self.consumer.page_count + 1
                self.logger.info('Found %d current events in %s' %
                        (self.consumer.total_items, self.location))
                self.logger.info('Fetched %d pages (%d events per page) ...' %
                        (last_page - self.current_page, self.page_size))
                self.logger.info('Starting from page %d/%d' %
                        (self.current_page, self.consumer.page_count))
                fetched_meta = True

            if self.interactive:
                self.logger.info('Import this page into database? \n (Y/n)')
                cmd_str = raw_input()
                if not cmd_str:
                    fetch_next = True
                else:
                    fetch_next = True if 'y' in cmd_str.lower() else False
            else:
                fetch_next = True

            if fetch_next:
                for event in events:
                    # try:
                    self.process_event(event)
                    event_obj = self.parser.parse(event)
                        # THIS IS VERY UGLY
                    # FIXME
                    # HANDLE THA DAMN EXCEPTIONS
                    # except Exception as e:
                        # import ipdb; ipdb.set_trace()
                        # raise e
                        # self.logger.warn("Encountered %s exception while parsing" %
                                # type(exception))
                self.logger.info('Fetched %d/%d events so far' %
                        (self.count, self.consumer.total_items))

            self.current_page += 1

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
