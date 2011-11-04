import datetime
import json
import logging
import urllib
import pprint
from django.contrib.gis import geos
from api.models import Consumer
from behavior.models import EventAction, EventActionAggregate
from importer.models import Category
from django.conf import settings
from django.test import TestCase
from django.test.client import Client
from django_dynamic_fixture import get, new, DynamicFixture as F

from events.models import Event, Occurrence
# from prices.models import Price
from places.models import City, Point, Place

TEST_LOGGER = logging.getLogger('api.test')

API_VERSION = 'v1'
API_BASE_URL = '/api'

def build_url(endpoint):
    return '/'.join((API_BASE_URL, API_VERSION, endpoint))

class EventRecommendationTest(TestCase):
    fixtures = ['auth', 'consumers', 'categories']
    url = build_url('eventrecommendation/') 
    def setUp(self):
        consumer = Consumer.objects.get(id=1)
        self.encoded_params = '?'
        self.encoded_params += urllib.urlencode({'consumer_key': consumer.key,
                                            'consumer_secret': consumer.secret,
                                            'udid': '6AAD4638-7E07-5A5C-A676-3D16E4AFFAF3'
        })
        # events = [str(e.id) for e in Event.objects.all()]
        self.client = Client()
        settings.DEBUG = True

    def test_initial_event_recommendation(self):
        category = Category.objects.filter(title='Sports & Recreation')[0]
        for loop in range(20):
            event_title = str(loop)
            event = get(Event, occurrences=[],
                    concrete_category=category, title=event_title)
            occurrence = get(Occurrence, start_date=datetime.date(2063, 1, 1),
                        start_time=datetime.time(15, 0),
                        place=F(point=F(geometry=geos.Point(y=40.7601,
                            x=-73.9925))), event=event)
            # event = get(Event, occurrences=[F(start_date=datetime.date(2063, 1, 1),
                        # start_time=datetime.time(15, 0),
                        # place=F(point=F(geometry=geos.Point(y=40.7601,
                            # x=-73.9925))))], concrete_category=category)
            event.save()

        resp = self.client.get(self.url + self.encoded_params)
        json_resp = json.loads(resp.content)

        event_titles = set(e.title for e in Event.objects.all())
        produced_event_titles = set(e['title'] for e in json_resp['objects'])

        self.assertEqual(event_titles, produced_event_titles,
                'Unexpected initial recommended events set')

        TEST_LOGGER.info(pprint.pprint(json_resp))

    def test_event_action_persisted(self):
        category = Category.objects.filter(title='Sports & Recreation')[0]
        event_titles = []
        for loop in range(20):
            event_title = str(loop)
            event = get(Event, occurrences=[],
                    concrete_category=category, title=event_title)
            occurrence = get(Occurrence, start_date=datetime.date(2063, 1, 1),
                        start_time=datetime.time(15, 0),
                        place=F(point=F(geometry=geos.Point(y=40.7601,
                            x=-73.9925))), event=event)
            event_titles.append(event_title)
            event.save()

        resp = self.client.get(self.url + self.encoded_params)
        resp_dict = json.loads(resp.content)


        action_url = build_url('eventaction/')
        event_uri = resp_dict['objects'][7]['event']
        import ipdb; ipdb.set_trace()

        json_params = json.dumps(dict(action='v', event=event_uri)) 
        for loop in range(2):
            action_resp = self.client.post(action_url + self.encoded_params,
                    json_params,
                    content_type='application/json')
            self.assertEqual(201, action_resp.status_code,
                    'Unexpected HTTP status code for event action')

        self.assertGreater(EventAction.objects.count(), 0, 'Unexpected failure of EventAction objects to be persisted')

        go_count = EventAction.objects.filter(action='G').count()
        view_count = EventAction.objects.filter(action='V').count()
        ignore_count = EventAction.objects.filter(action='I').count()
        delete_count = EventAction.objects.filter(action='X').count()

        self.assertGreater(EventActionAggregate.objects.count(), 0, 'Unexpected failure of EventActionAggregate object to be created')
        event_action_aggregate = EventActionAggregate.objects.all()[0]

        self.assertEqual(go_count, event_action_aggregate.g, 'Incorrect aggregate count of GO actions')
        self.assertEqual(view_count, event_action_aggregate.v, 'Incorrect aggregate count of VIEW actions')
        self.assertEqual(ignore_count, event_action_aggregate.i, 'Incorrect aggregate count of IGNORE actions')
        self.assertEqual(delete_count, event_action_aggregate.x, 'Incorrect aggregate count of DELETE actions')

        resp = self.client.get(self.url + self.encoded_params)
        json_resp = json.loads(resp.content)

        # TEST_LOGGER.info(pprint.pprint(json_resp))

