import logging
from importer.api.eventful import conf
from importer.api.eventful.adaptors import EventAdaptor
from importer.api.eventful.client import APIError
from importer.api.eventful.consumer import EventfulApiConsumer


class EventfulPaginator(object):
    logger = logging.getLogger('importer.api.eventful.paginator')

    def __init__(self, interactive=None, total_pages=None, start_page=1,
            silent_fail=None, consumer_kwargs=None, client_kwargs=None, query_kwargs=conf.IMPORT_PARAMETERS):
        # internal initializations
        self.consumer = EventfulApiConsumer(client_kwargs=client_kwargs, **(consumer_kwargs or {}))
        self.event_adaptor = EventAdaptor()
        self.events = []
        self.interactive = interactive
        self.total_pages = total_pages
        self.start_page = start_page
        self.query_kwargs = query_kwargs
        self.event_horizon = None
        self.silent_fail = silent_fail

    def _import_page_events(self, page_data, interactive, silent_fail):
        # Is interactive mode set? If so, then ask whether to import the
        # current page. This happens after the page is fetched.
        results = []
        import_this_page = True
        if interactive:
            self.logger.info('Import this page into database? \n (Y/n)')
            cmd_str = raw_input()
            if cmd_str:
                import_this_page = cmd_str.lower().startswith('y')
        if import_this_page:
            for event in page_data:
                if not silent_fail:
                    created, event_obj = self.event_adaptor.adapt(event)
                    results.append((created, event_obj.id))
                else:
                    try:
                        created, event_obj = self.event_adaptor.adapt(event)
                        results.append((created, event_obj.id))
                    except Exception as e:
                        self.logger.error(e)
        else:
            self.logger.info('Did not import events from this page')
        return results

    def import_events(self):
        self.logger.info('Beginning import of eventful events...')

        search_meta = self.consumer.consume_meta(self.query_kwargs)

        # if no amount of pages to fetch is given, default to all

        pages_available = search_meta['page_count']

        if not self.total_pages:
            self.total_pages = pages_available
        if self.start_page + self.total_pages - 1 > pages_available:
            self.total_pages = max(0, pages_available - self.start_page + 1)


        # estimated maximum number of calls: 2 per event (worst case scenario
        # needing to make call for event and venue details each time), 1 per
        # page

        estimated_calls = 2 * self.total_pages * self.query_kwargs['page_size'] + self.total_pages

        self.logger.info('Number of matching the search results: %s', search_meta['total_items'])
        self.logger.info('Will fetch: %s pages (%s events per page)',
                         self.total_pages, self.query_kwargs['page_size'])
        self.logger.info('Starting from page: %s (%s available)', self.start_page, pages_available)
        self.logger.info('Estimated maximum number of calls required for entire resultset: %s', estimated_calls)

        results = []

        if estimated_calls > conf.SAFE_API_CALL_LIMIT:
            continue_fetch = False
            self.logger.warn("Estimated API calls exceeds safe limit: %s", conf.SAFE_API_CALL_LIMIT)
            if not self.consumer.trust:
                self.logger.warn("Continue to fetch? (y/N)")
                cmd_str = raw_input()
                if cmd_str:
                    continue_fetch = cmd_str.lower().startswith('y')
                if not continue_fetch:
                    return results

        for page_number in range(self.start_page, self.start_page + self.total_pages):
            self.query_kwargs['page_number'] = page_number
            try:
                self.logger.info('Fetching page number: %s (%s available)', page_number, pages_available)
                events = self.consumer.consume(self.query_kwargs)
            except APIError as e:
                self.logger.exception(e)
                break

            # Is interactive mode set? If so, then ask whether to import the
            # current page. This happens after the page is fetched.
            import_this_page = True
            if self.interactive:
                self.logger.info('Import this page into database? \n (Y/n)')
                cmd_str = raw_input()
                if cmd_str:
                    import_this_page = cmd_str.lower().startswith('y')
            if import_this_page:
                results.extend(self._import_page_events(events,
                    self.interactive, self.silent_fail))
            else:
                self.logger.info('Did not import events from this page')

        return results
