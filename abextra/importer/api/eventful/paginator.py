import logging
import datetime
from importer.api.eventful import conf 
from importer.api.eventful.adaptors import EventAdaptor
from importer.api.eventful.consumer import EventfulApiConsumer

class EventfulPaginator(object):
    def __init__(self, interactive=False, total_pages=None, page_number=1,
                 consumer_kwargs=None, client_kwargs=None, query_kwargs=conf.IMPORT_PARAMETERS):
        # internal initializations
        self.consumer = EventfulApiConsumer(client_kwargs=client_kwargs, **(consumer_kwargs or {}))
        self.parser = EventAdaptor()
        self.logger = logging.getLogger('importer.eventful_import')
        self.count = 0
        self.events = []
        self.interactive = interactive
        self.total_pages = total_pages
        self.page_number = page_number
        self.query_kwargs = query_kwargs
        self.event_horizon = None


    def import_events(self):
        self.logger.info('Beginning import of eventful events...')

        results = []
        fetched_meta, stop_page = False, self.page_number + 1
        while self.page_number < stop_page:
            self.query_kwargs['page_number'] = self.page_number
            events = self.consumer.consume(self.query_kwargs)

            # Check at the beginning of the import to set stop page for  
            # fetching, because that controls how many times the page fetching/parsing
            # logic will loop.

            if not fetched_meta:
                if not self.total_pages:
                    stop_page = self.consumer.page_count + 1
                else:
                    stop_page = self.page_number + self.total_pages
                    if stop_page > self.consumer.page_count + 1:
                        stop_page = self.consumer.page_count + 1
                self.logger.info('Found %d current events in %s' %
                                 (self.consumer.total_items, self.query_kwargs['location']))
                self.logger.info('Fetched %d pages (%d events per page) ...' %
                                 (stop_page - self.page_number, self.query_kwargs['page_size']))
                self.logger.info('Starting from page %d/%d (%d available)' %
                                 (self.page_number, stop_page - 1, self.consumer.page_count))
                self.logger.info('Estimated maximum of %d calls needed to fetch current import batch' %
                                 (2 * (stop_page - self.page_number) * self.query_kwargs['page_size'] + (stop_page - self.page_number) + 1))
                fetched_meta = True

            # Is interactive mode set? If so, then ask whether to import the
            # current page. This happens after the page is fetched.
            fetch_next = True
            if self.interactive:
                self.logger.info('Currently on page %d/%d (%d available)' %
                                 (self.page_number, stop_page - 1, self.consumer.page_count))
                self.logger.info('Import this page into database? \n (Y/n)')
                cmd_str = raw_input()
                if cmd_str:
                    fetch_next = cmd_str.lower().startswith('y')

            # If the page has been fetched, then go through each event and
            # parse occurrences from that event. Using process_event,
            # preprocess the event and then attempt to parse it.

            if fetch_next:
                # process all events on the page, putting them into separate
                # buckets of created and existing objects
                for event in events:
                    # increase event counter
                    self.count += 1
                    created, event_obj = self.parser.parse(event)
                    results.append((created, event_obj.id))

                self.logger.info('Fetched %d/%d events so far' %
                                 (self.count, self.consumer.total_items))
            else:
                self.logger.info('Did not import events from this page')

            # increase the page counter
            self.page_number += 1
        return results
