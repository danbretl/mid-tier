import eventlet
import itertools
import datetime
import logging
from importer.api.eventful import conf
from importer.api.eventful.client import API, MockAPI

class EventfulApiConsumer(object):
    """Eventful API consumer is the driver of the Eventful API.
    Uses eventlets to achieve non-blocking (async) API requests.
    """

    def __init__(self, mock_api=False, trust=False, client_kwargs=None):
        # instantiate api
        api_class = MockAPI if mock_api else API
        self.api = api_class(**(client_kwargs or {}))
        self.logger = logging.getLogger('importer.api.eventful.consumer')
        self.total_items = None
        self.page_count = None
        self.event_horizon = None
        self.api_calls = 0
        self.trust = trust

        self.venue_ids = set()
        self.images_by_event_id = {}
        self.images_by_venue_id = {}
        self.venues_by_venue_id = {}

        # a green pile for images w/ fairly high concurrency
        # (webservers are ok with it)
        self.event_image_pile = eventlet.GreenPile(15)
        # a green pile for event details w/ lower concurrency
        # (appservers are not too ok with it)
        self.event_detail_pile = eventlet.GreenPile(10)
        # a green pile for venue images w/ fairly high concurrency
        # (webservers are ok with it)
        self.venue_image_pile = eventlet.GreenPile(15)
        # a green pile for venue details w/ lower concurrency
        # (appservers are not too ok with it)
        self.venue_detail_pile = eventlet.GreenPile(10)

    def fetch_event_summaries(self, query_kwargs):
        self.api_calls += 1
        resp = self.api.call('/events/search', **query_kwargs)
        return resp

    def process_event_summaries(self, summaries):
        limit = conf.API_CALL_LIMIT if self.trust else conf.API_CALL_LIMIT/2
        self.logger.debug('%d/%d eventful API calls made so far',self.api_calls, conf.API_CALL_LIMIT)
        if isinstance(summaries, (list, tuple)):
            for summary in summaries:
                if self.api_calls >= limit:
                    self.logger.warn('Current number of calls %d matches or exceeds API call limit %d',
                            self.api_calls, conf.API_CALL_LIMIT)
                    return
                self.process_event_summary(summary)
        else:
            self.process_event_summary(summaries)

    def process_event_summary(self, summary):
        # schedule a fetch of event details
        self.event_detail_pile.spawn(self.fetch_event_details, summary['id'])
        # schedule a fetch of venue details + image
        if not summary['venue_id'] in self.venue_ids:
            self.venue_detail_pile.spawn(self.fetch_venue_details, summary['venue_id'])
            self.venue_ids.add(summary['venue_id'])

    def fetch_venue_details(self, venue_id, fetch_images=True):
        self.api_calls += 1
        venue_detail = self.api.call('/venues/get', id=venue_id)
        images = venue_detail.get('images')
        if images and fetch_images:
            self.venue_image_pile.spawn(self.api.fetch_image, images, venue_id)
        return venue_detail

    def fetch_event_details(self, event_id, fetch_images=True):
        self.api_calls += 1
        event_detail = self.api.call('/events/get', id=event_id,
                                     include='instances')
        images = event_detail.get('images')
        if images and fetch_images:
            self.event_image_pile.spawn(self.api.fetch_image, images, event_id)
        return event_detail

    def consume_meta(self, query_kwargs):
        initial_page, initial_size = query_kwargs.get('page_number'), query_kwargs.get('page_size')
        query_kwargs['page_number'], query_kwargs['page_size'] = 1, 1

        # Prepare event horizon
        if not self.event_horizon:
            current_datetime = datetime.datetime.now()
            self.event_horizon = current_datetime, current_datetime + conf.IMPORT_EVENT_HORIZON

        if not query_kwargs.get('date'):
            horizon_start, horizon_stop = self.event_horizon
            query_kwargs['date'] = self.api.daterange_query_param(
                horizon_start, horizon_stop)

        response = self.fetch_event_summaries(query_kwargs)


        raw_summaries = response['events']['event']
        self.total_items = int(response['total_items'])
        self.page_count = int(response['page_count'])

        # Only fetching metadata, so don't process summaries

        query_kwargs['page_number'], query_kwargs['page_size'] = initial_page, initial_size


    def consume(self, query_kwargs):
        # Prepare event horizon
        if not self.event_horizon:
            current_datetime = datetime.datetime.now()
            self.event_horizon = current_datetime, current_datetime + conf.IMPORT_EVENT_HORIZON

        if not query_kwargs.get('date'):
            horizon_start, horizon_stop = self.event_horizon
            query_kwargs['date'] = self.api.daterange_query_param(
                horizon_start, horizon_stop)

        response = self.fetch_event_summaries(query_kwargs)
        raw_summaries = response['events']['event']
        self.total_items = int(response['total_items'])
        self.page_count = int(response['page_count'])
        self.process_event_summaries(raw_summaries)

        self.images_by_event_id.update(dict((img['id'], img) for img in self.event_image_pile if img))
        self.images_by_venue_id.update(dict((img['id'], img) for img in self.venue_image_pile if img))
        self.venues_by_venue_id.update(dict((v['id'], v) for v in self.venue_detail_pile if v))

        def extend_with_details(event):
            event.setdefault('__kwiqet', {})
            event_images = self.images_by_event_id.get(event['id'])
            if event_images:
                event['__kwiqet']['event_images'] = [event_images]
            venue_id = event.get('venue_id')
            if venue_id:
                event['__kwiqet']['venue_details'] = self.venues_by_venue_id[venue_id]
                venue_images = self.images_by_venue_id.get(event['venue_id'])
                if venue_images:
                    event['__kwiqet']['venue_images'] = [venue_images]
            if self.event_horizon:
                event['__kwiqet']['horizon_start'], event['__kwiqet']['horizon_stop'] = self.event_horizon
            return event

        events = itertools.imap(extend_with_details, self.event_detail_pile)
        return events
