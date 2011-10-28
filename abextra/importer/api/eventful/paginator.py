import logging
import math
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

        # want to make metadata fetching call with page_size=1 and page_number=1
        events_meta = self.consumer.consume_meta(self.query_kwargs)

        # if no amount of pages to fetch is given, default to all
        pages_available = int(math.ceil(float(self.consumer.page_count)/self.query_kwargs['page_size']))
        if not self.total_pages:
            self.total_pages = pages_available

        # estimated maximum number of calls: 2 per event (worst case scenario
        # needing to make call for event and venue details each time), 1 per
        # page, and 1 for metadata

        estimated_calls = 2 * self.total_pages * self.query_kwargs['page_size'] + self.total_pages + 1 

        self.logger.info('Found %d current events in %s',
                self.consumer.total_items, self.query_kwargs['location'])
        self.logger.info('Fetching %d pages (%d events per page) ...',
                self.total_pages, self.query_kwargs['page_size'])
        self.logger.info('Starting from page %d/%d (%d available)',
                self.page_number, self.total_pages, pages_available)
        self.logger.info('Estimated maximum of %d calls needed to fetch current batch',
                estimated_calls) 
        if estimated_calls > conf.API_CALL_LIMIT/2:
            continue_fetch = False
            self.logger.warn("Estimated API calls exceeds limit(%d)/2", conf.API_CALL_LIMIT)
            if not self.consumer.trust:
                self.logger.warn("Continue to fetch? (y/N)")
                cmd_str = raw_input()
                if cmd_str:
                    continue_fetch = cmd_str.lower().startswith('y')
                if not continue_fetch:
                    return results

        stop_page = self.page_number + self.total_pages - 1 
        while self.page_number <= stop_page:
            if self.consumer.api_calls >= (conf.API_CALL_LIMIT if self.consumer.trust else conf.API_CALL_LIMIT/2):
                break
            self.query_kwargs['page_number'] = self.page_number
            events = self.consumer.consume(self.query_kwargs)

            # Check at the beginning of the import to set stop page for  
            # fetching, because that controls how many times the page fetching/parsing
            # logic will loop.
            # Is interactive mode set? If so, then ask whether to import the
            # current page. This happens after the page is fetched.
            fetch_next = True
            if self.interactive:
                self.logger.info('Currently on page %d/%d (%d available)' %
                                 (self.page_number, stop_page, self.consumer.page_count))
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
