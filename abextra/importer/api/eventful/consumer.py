import eventlet
import itertools
from django.conf import settings
from importer.api.eventful.client import API, MockAPI

class EventfulApiConsumer(object):
    """Eventful API consumer is the driver of the Eventful API.
    Uses eventlets to achieve non-blocking (async) API requests.
    """
    def __init__(self, mock_api=False,
                 make_dumps=False):
        # instantiate api
        api_class = MockAPI if mock_api else API
        self.api = api_class(make_dumps=make_dumps)
        self.total_items = None
        self.page_count = None

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

    def fetch_event_summaries(self, **kwargs):
        resp = self.api.call('/events/search', **kwargs)
        return resp

    def process_event_summaries(self, summaries):
        if isinstance(summaries, (list, tuple)):
            for summary in summaries:
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
        venue_detail = self.api.call('/venues/get', id=venue_id)
        images = venue_detail.get('images')
        if images and fetch_images:
            self.venue_image_pile.spawn(self.api.fetch_image, images, venue_id)
        return venue_detail

    def fetch_event_details(self, event_id, fetch_images=True):
        event_detail = self.api.call('/events/get', id=event_id,
                include='instances')
        images = event_detail.get('images')
        if images and fetch_images:
            self.event_image_pile.spawn(self.api.fetch_image, images, event_id)
        return event_detail

    def consume(self, **kwargs):
        response = self.fetch_event_summaries(**kwargs)
        raw_summaries = response['events']['event']
        self.total_items = int(response['total_items'])
        self.page_count = int(response['page_count'])
        self.process_event_summaries(raw_summaries)

        self.images_by_event_id.update(dict((img['id'], img) for img in self.event_image_pile if img))
        self.images_by_venue_id.update(dict((img['id'], img) for img in self.venue_image_pile if img))
        self.venues_by_venue_id.update(dict((v['id'], v) for v in self.venue_detail_pile if v))

        def extend_with_details(event):
            event_images = self.images_by_event_id.get(event['id'])
            if event_images:
                event['event_images_local'] = [event_images]

            venue_id = event.get('venue_id')
            if venue_id:
                event['venue_details'] = self.venues_by_venue_id[venue_id]
                venue_images = self.images_by_venue_id.get(event['venue_id'])
                if venue_images:
                    event['venue_images_local'] = [venue_images]
            return event

        events = itertools.imap(extend_with_details, self.event_detail_pile)
        return events
