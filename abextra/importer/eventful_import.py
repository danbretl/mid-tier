import logging
import itertools
from django.conf import settings
from importer.parsers.eventful import EventfulEventParser
from importer.eventful_api.loader import EventfulApiConsumer
import events.models

class EventfulImporter(object):

    def __init__(self, current_page=1, page_size=100, total_pages=0, query='', location='NYC', mock_api=False, interactive=False, make_dumps=False):
        dump_sub_dir = 'p%d-c%d' % (total_pages, page_size)
        self.consumer = EventfulApiConsumer(api_key=settings.EVENTFUL_API_KEY,
                mock_api=mock_api, make_dumps=make_dumps,
                dump_sub_dir=dump_sub_dir)
        self.parser = EventfulEventParser()
        self.logger = logging.getLogger('importer.eventful_import')
        self.count = 0
        self.events = []
        self.page_size = page_size
        self.query = query
        self.location = location
        self.current_page = current_page
        self.interactive = interactive
        self.total_pages = total_pages

    def import_events(self):

        created_event_objs = []
        existing_event_objs = []

        stop_page = self.page_size + 1
        fetched_meta = False

        self.logger.info('Beginning import of eventful events...') 

        while self.current_page < stop_page:
            events = self.consumer.consume(location=self.location, date='Today',
                page_size=self.page_size, page_number=self.current_page)

            # Check at the beginning of the import to set stop page for  
            # fetching, because that controls how many times the page fetching/parsing
            # logic will loop.

            if not fetched_meta:
                if not self.total_pages:
                    stop_page = self.consumer.page_count + 1
                else:
                    stop_page = self.current_page + self.total_pages
                    if stop_page > self.consumer.page_count + 1:
                        stop_page = self.consumer.page_count + 1
                self.logger.info('Found %d current events in %s' %
                        (self.consumer.total_items, self.location))
                self.logger.info('Fetched %d pages (%d events per page) ...' %
                        (stop_page - self.current_page, self.page_size))
                self.logger.info('Starting from page %d/%d (%d available)' %
                        (self.current_page, stop_page - 1, self.consumer.page_count))
                fetched_meta = True

            # Is interactive mode set? If so, then ask whether to import the
            # current page. This happens after the page is fetched.

            if self.interactive:
                self.logger.info('Currently on page %d/%d (%d available)' %
                        (self.current_page, stop_page - 1, self.consumer.page_count))
                self.logger.info('Import this page into database? \n (Y/n)')
                cmd_str = raw_input()
                if not cmd_str:
                    fetch_next = True
                else:
                    fetch_next = True if 'y' in cmd_str.lower() else False
            else:
                fetch_next = True

            # If the page has been fetched, then go through each event and
            # parse occurrences from that event. Using process_event,
            # preprocess the event and then attempt to parse it.

            if fetch_next:
                for event in events:
                    # try:
                    self.process_event(event)
                    created, event_obj = self.parser.parse(event)
                    if created:
                        created_event_objs.append(event_obj)
                    elif not created and event_obj:
                        existing_event_objs.append(event_obj)
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
        return (created_event_objs, existing_event_objs)

    # FIXME: implement JSON dump events & settings
    def json_dump():
        pass

    # FIXME: implement JSON load events & settings
    def json_load():
        pass

    def process_event(self, e):
        # preprocess event response
        self.count += 1
        return e
        # pass
