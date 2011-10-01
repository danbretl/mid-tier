import os
import eventlet
import itertools
from django.conf import settings
from eventlet.green import urllib, urllib2
from eventful_api import API

class SimpleApiConsumer(object):
    def __init__(self, img_dir=settings.SCRAPE_IMAGES_PATH, api_key='D9knBLC95spxXSqr'):
        # instantiate api
        self.api = API(api_key)

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
        self.venue_detail_pile= eventlet.GreenPile(10)

        # prepare image download directory
        if not os.path.exists(img_dir):
            os.makedirs(img_dir)
        self.img_dir = img_dir

    def fetch_event_summaries(self, **kwargs):
        resp = self.api.call('/events/search', **kwargs)
        return resp['events']

    def process_event_summaries(self, summaries):
        for summary in summaries:
            self.process_event_summary(summary)

    def process_event_summary(self, summary):
        # schedule a fetch of event details
        self.event_detail_pile.spawn(self.fetch_event_details, summary['id'])
        # schedule a fetch of venue details + image
        self.venue_detail_pile.spawn(self.fetch_venue_details, summary['venue_id'])

    def fetch_venue_details(self, venue_id):
        venue_detail = self.api.call('/venues/get', id=venue_id)
        images = venue_detail.get('images')
        if images:
            self.venue_image_pile.spawn(self.fetch_image, images, venue_id)
        return venue_detail
        # return 'test'

    def fetch_event_details(self, event_id):
        event_detail = self.api.call('/events/get', id=event_id)
        images = event_detail.get('images')
        if images:
            self.event_image_pile.spawn(self.fetch_image, images, event_id)
        return event_detail


    def fetch_image(self, images_dict, parent_id):
        img_dict = images_dict.get('image')
        # import ipdb; ipdb.set_trace()
        if isinstance (img_dict, (tuple, list)):
            url = img_dict[0]['small']['url'].replace('small', 'original')
        else:
            url = img_dict['small']['url'].replace('small', 'original')
        request = urllib2.Request(url)
        try:
            img = urllib2.urlopen(request)
        except (urllib2.URLError, urllib2.HTTPError), e:
            # FIXME: use logger to print these error messages
            print "HTTP Error:", e.code, url
        else:
            filename = os.path.join(self.img_dir, parent_id+'.png')
            with open(filename, 'w') as f:
                f.write(img.read())
            return dict(id=parent_id, filename=filename, url=url)

    def consume(self, **kwargs):
        images_by_event_id = {}
        raw_summaries = self.fetch_event_summaries(**kwargs)['event']
        self.process_event_summaries(raw_summaries)
        images_by_event_id = dict((img['id'], img) for img in self.event_image_pile if img)
        images_by_venue_id = dict((img['id'], img) for img in self.venue_image_pile if img)
        # import ipdb; ipdb.set_trace()
        venues_by_venue_id = dict((v['id'], v) for v in self.venue_detail_pile if v)
        def extend_with_details(event):
            image_local = images_by_event_id.get(event['id'])
            if image_local:
                event['image_local'] = image_local

            venue_id = event.get('venue_id')
            if venue_id:
                event['venue_details'] = venues_by_venue_id[venue_id]
                venue_image_local = images_by_venue_id.get(event['venue_id'])
                if venue_image_local:
                    event['venue_details']['image_local'] = venue_image_local
            return event
        events = itertools.imap(extend_with_details, self.event_detail_pile)
        # import ipdb; ipdb.set_trace()
        return events

