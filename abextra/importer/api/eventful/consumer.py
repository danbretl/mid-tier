import eventlet
import itertools
import datetime
import logging
from importer.api.eventful import conf
from importer.api.eventful.client import API, MockAPI, APIError

class EventfulApiConsumer(object):
    """Eventful API consumer is the driver of the Eventful API.
    Uses eventlets to achieve non-blocking (async) API requests.
    """

    def __init__(self, mock_api=False, trust=False, client_kwargs=None):
        # instantiate api
        api_class = MockAPI if mock_api else API
        self.api = api_class(**(client_kwargs or {}))
        self.logger = logging.getLogger('importer.api.eventful.consumer')
        self.event_horizon = None
        self.trust = trust
        self.client_call_limit = conf.API_CALL_LIMIT if self.trust else conf.SAFE_API_CALL_LIMIT

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

    def search_events(self, query_kwargs):
        # prepare event horizon
        if not self.event_horizon:
            current_datetime = datetime.datetime.now()
            # make instance scope to avoid recalculating the value when paginated
            self.event_horizon = current_datetime, current_datetime + conf.IMPORT_EVENT_HORIZON

        if not query_kwargs.get('date'):
            horizon_start, horizon_stop = self.event_horizon
            query_kwargs['date'] = self.api.daterange_query_param(horizon_start, horizon_stop)

        return self.api.call('/events/search', **query_kwargs)

    def process_event_summaries(self, summaries):
        summaries = summaries if isinstance(summaries, list) else [summaries]
        for summary in summaries:
            if self.api.CALL_COUNT >= self.client_call_limit:
                raise APIError('Call limit reached | %s.' % self.client_call_limit)
            self.process_event_summary(summary)

    def process_event_summary(self, summary):
        # schedule a fetch of event details
        self.event_detail_pile.spawn(self.fetch_event_details, summary['id'])
        # schedule a fetch of venue details + image
        if not summary['venue_id'] in self.venue_ids:
            self.venue_detail_pile.spawn(self.fetch_venue_details, summary['venue_id'])
            self.venue_ids.add(summary['venue_id'])

    def fetch_venue_details(self, venue_id, fetch_images=True):
        venue_detail = self.api.call('/venues/get', id=venue_id)
        images = venue_detail.get('images')
        if images and fetch_images:
            self.venue_image_pile.spawn(self.api.fetch_image, images, venue_id)
        return venue_detail

    def fetch_event_details(self, event_id, fetch_images=True):
        event_detail = self.api.call('/events/get', id=event_id, include='instances')
        images = event_detail.get('images')
        if images and fetch_images:
            self.event_image_pile.spawn(self.api.fetch_image, images, event_id)
        return event_detail

    def consume_meta(self, query_kwargs):
        meta_query_kwargs = dict(query_kwargs, **dict(page_number=1, page_size=1))
        response = self.search_events(meta_query_kwargs)
        raw_meta = dict((k, v) for k, v in response.iteritems() if not k in ('events',))
        raw_page_count = int(raw_meta['page_count'])
        meta_page_size = int(query_kwargs['page_size']) or 1
        corrected_page_count = (raw_page_count / meta_page_size) + (1 if raw_page_count % meta_page_size else 0)
        return dict(page_count=corrected_page_count, total_items=int(raw_meta['total_items']))

    def consume(self, query_kwargs):
        response = self.search_events(query_kwargs)
        raw_summaries = (response.get('events') or {}).get('event')
        if not raw_summaries:
            return []
        self.process_event_summaries(raw_summaries)
        self.images_by_event_id.update(dict((img['id'], img) for img in self.event_image_pile if img))
        self.images_by_venue_id.update(dict((img['id'], img) for img in self.venue_image_pile if img))
        self.venues_by_venue_id.update(dict((v['id'], v) for v in self.venue_detail_pile if v))
        return itertools.imap(self._extend_with_details, self.event_detail_pile)

    def _extend_with_details(self, event):
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
