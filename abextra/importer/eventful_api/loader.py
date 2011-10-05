import os
import eventlet
import itertools
from PIL import Image
from StringIO import StringIO
from django.conf import settings
from eventlet.green import urllib, urllib2
from eventful_api import API

class SimpleApiConsumer(object):
    def __init__(self, img_dir=os.path.join(settings.SCRAPE_FEED_PATH, settings.SCRAPE_IMAGES_PATH), api_key='D9knBLC95spxXSqr'):
        # instantiate api
        self.api = API(api_key)
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

        # prepare image download directory
        if not os.path.exists(img_dir):
            os.makedirs(img_dir)
        self.img_dir = img_dir

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

    def fetch_venue_details(self, venue_id):
        venue_detail = self.api.call('/venues/get', id=venue_id)
        images = venue_detail.get('images')
        if images:
            self.venue_image_pile.spawn(self.fetch_image, images, venue_id)
        return venue_detail

    def fetch_event_details(self, event_id):
        event_detail = self.api.call('/events/get', id=event_id)
        images = event_detail.get('images')
        if images:
            self.event_image_pile.spawn(self.fetch_image, images, event_id)
        return event_detail

    def fetch_image(self, images_dict, parent_id):
        img_dict = images_dict.get('image')
        if isinstance (img_dict, (tuple, list)):
            url = img_dict[0]['small']['url'].replace('small', 'original')
        else:
            url = img_dict['small']['url'].replace('small', 'original')
        request = urllib2.Request(url)
        try:
            img = urllib2.urlopen(request)
        except (urllib2.URLError, urllib2.HTTPError), e:
            # FIXME: use logger to print these error messages
            print "Internets Error:", url
        else:
            img_dat = img.read()
            im = Image.open(StringIO(img_dat))
            width, height = im.size
            # FIXME: migrate image dimension checking logic to form so that it
            # can be reused
            if width >= settings.IMAGE_MIN_DIMS['width'] and height >= settings.IMAGE_MIN_DIMS['height']:
                suffix = '.'+url.split('.')[-1]
                filename = os.path.join(self.img_dir, parent_id+suffix)
                with open(filename, 'w') as f:
                    f.write(img_dat)
                return dict(id=parent_id, path=filename, url=url)
            else:
                print 'Image %s did not meet minimum image dimensions; discarding' % parent_id

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
            image_local = self.images_by_event_id.get(event['id'])
            if image_local:
                event['image_local'] = [image_local]

            venue_id = event.get('venue_id')
            if venue_id:
                event['venue_details'] = self.venues_by_venue_id[venue_id]
                venue_image_local = self.images_by_venue_id.get(event['venue_id'])
                if venue_image_local:
                    event['venue_image_local'] = [venue_image_local]
            return event
        events = itertools.imap(extend_with_details, self.event_detail_pile)
        return events

