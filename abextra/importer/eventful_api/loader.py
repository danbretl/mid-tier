import os
import eventlet
from eventlet.green import urllib, urllib2
from eventful_api import API

class SimpleApiConsumer(object):
    def __init__(self, img_dir='images'):
        # instantiate api
        self.api = API('D9knBLC95spxXSqr')

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

    def consume(self, **kwargs):
        raw_summaries = self.fetch_event_summaries(**kwargs)['event']
        self.process_event_summaries(raw_summaries)
        return self.event_pile

if __name__ == '__main__':
    consumer = SimpleApiConsumer()
    events = consumer.consume(location='NYC', date='Today', page_size=20)
    imgs = dict((img['id'], img) for img in consumer.image_pile)
    import ipdb; ipdb.set_trace()
    # at this point you should have all the necessary event details + images
    # all that's needed to create our own events using parsers
    for e_k in events.keys():
        events['image']['path'] = imgs.filename
        events['image']['url'] = imgs.url
    print list(events)
