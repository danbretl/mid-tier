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
        self.image_pile = eventlet.GreenPile(30)
        # a green pile for event details w/ lower concurrency
        # (appservers are not too ok with it)
        self.event_pile = eventlet.GreenPile(15)

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
        self.event_pile.spawn(self.fetch_event_details, summary['id'])
        # schedule a fetch of the event image
        if summary.get('image'):
            self.image_pile.spawn(self.fetch_event_image, summary)

    def fetch_event_details(self, event_id):
        return self.api.call('/events/get', id=event_id)

    def fetch_event_image(self, event):
        img_dict = event.get('image')
        url = img_dict['url'].replace('small', 'edpborder500')
        request = urllib2.Request(url)
        try:
            img = urllib2.urlopen(request)
        except urllib2.HTTPError, e:
            print "HTTP Error:", e.code, url
        except urllib2.URLError, e:
            print "URL Error:", e.reason, url
        else:
            filename = os.path.join(self.img_dir, event['id']+'.png')
            with open(filename, 'w') as f:
                f.write(img.read())
            return dict(id=event['id'], filename=filename, url=url)
        return dict(id=event['id'], filename=None, url=url)
    def consume(self, **kwargs):
        images_by_event_id = {}
        raw_summaries = self.fetch_event_summaries(**kwargs)['event']
        self.process_event_summaries(raw_summaries)
        images_by_event_id = dict((img['id'], img) for img in self.image_pile)
        def extend_with_image(event):
            image_local = images_by_event_id.get(event['id'])
            if image_local:
                event['image_local'] = image_local
            return event
        events = itertools.imap(extend_with_image, self.event_pile)
        # import ipdb; ipdb.set_trace()
        return events

