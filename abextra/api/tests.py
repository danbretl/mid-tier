"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
from api.models import Consumer
import urllib
from django.test import TestCase
from django.test.client import Client
from events.models import Event
import threading
import random
import json
import logging

class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)

def test_concurrently(times):
    """ 
    Add this decorator to small pieces of code that you want to test
    concurrently to make sure they don't raise exceptions when run at the
    same time.  E.g., some Django views that do a SELECT and then a subsequent
    INSERT might fail when the INSERT assumes that the data has not changed
    since the SELECT.
    """
    def test_concurrently_decorator(test_func):
        def wrapper(*args, **kwargs):
            exceptions = []
            import threading
            def call_test_func():
                try:
                    test_func(*args, **kwargs)
                except Exception, e:
                    exceptions.append(e)
                    raise
            threads = []
            for i in range(times):
                threads.append(threading.Thread())
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            if exceptions:
                raise Exception('test_concurrently intercepted %s exceptions: %s' % (len(exceptions), exceptions))
        return wrapper
    return test_concurrently_decorator



TEST_LOGGER = logging.getLogger('api.test')

class StressTesting(TestCase):
    """
    API's users will be hitting:
    1) Event_List
    2) Event_Detail
    3) CategoryFrequency
    4) BreadCrumbs
    5) Registration
    6) Sharing
    7) Haystack Search
    8) Event of the day page
    9) Event actions

    a) Test each API independently
    b) Test each API with a random ordering of the calls above
    c) Test each API with a expected sample of the calls above

    Serial stress test:
    a) Create a 1000 users
    b) For each of these users, generate a 100 requests
       - Randomly populate the user behavior db

    Concurrent stress test:
       - Same as above except, each user has his own process
         - Can a laptop handle 1000 processes?
           - Consider multithreading.

    To consider:
       - Distributed stress testing.

    Things to plot:
    a) Number of requests handled per second
    b) Average response time per request
    c) Users v/s load

    Stress testing individual components of the system:
    a) MySQL stress and performance tests under different query loads
    b) Django stress and performance tests under different query loads
       - Will be useful for before and after comparisons of Johnny Cache.
    c)

    #TODO: Create smaller fixtures for quick testing
    """
    fixtures_full = ['auth', 'consumers', 'events_all', 'categories', 'places', 'user', 'eventsummary', 'occurrences']
    fixtures = ['auth', 'consumers', 'events', 'categories', 'places', 'user', 'eventsummary']
    consumer = Consumer.objects.get(id=1)
    encoded_params = '?'
    encoded_params += urllib.urlencode({'consumer_key' : consumer.key,
                                        'consumer_secret' : consumer.secret,
                                        'udid' : '6AAD4638-7E07-5A5C-A676-3D16E4AFFAF3'
                                        })
    events = [str(e.id) for e in Event.objects.all()]
    client = Client()

    # Consider this for automated testing.
    def x_test_all_apis(self):
        base_url = 'http://testsv.abextratech.com'
        consumer_secret = '7fb49b90f41a832f3d5cc12f1b9ed56795c5748a'
        consumer_key = 'rngQ5ZSe3FmzYJ3cgL'
        udid = '6AAD4638-7E07-5A5C-A676-3D16E4AFFAF3'
        params = urllib.urlencode({'consumer_key' : consumer_key,
                                   'consumer_secret' : consumer_secret,
                                   'udid' : udid,
                                   'format': 'json'})
        # The more automated we want to make this the less assumptions we will
        # need to make.
        f = urllib.urlopen(base_url + '/api/v1/?' + params)
        apis = json.loads(f.readline())
        for model in apis.keys():
            #Test apis here
            schema_url = apis[model]['schema']
            list_endpoint = apis[model]['list_endpoint']
            schema = json.loads(urllib.urlopen( base_url
                                              + schema_url
                                              + params).readline())
            # Now hit the url and get some objects.
            # Ensure each of the URLS conforms to this schema
            # (such checks will likely have also been performed in tastypie's
            # unit tests)

    def x_simple_client_learn(self):
        clients = []
        num_clients = 100
        for num in range(num_clients):
            client = Client()
            clients.append(client)
        #1) Create fixtures for each of these
        apis_to_test = ['/api/v1/category/',
                        '/api/v1/city/',
                        '/api/v1/occurrence/',
                        '/api/v1/occurrence_full/',
                        '/api/v1/point/',
                        '/api/v1/point_full/',
                        '/api/v1/eventsummary/',
                        '/api/v1/eventaction/',
                        '/api/v1/event_full/',
                        '/api/v1/price/',
                        '/api/v1/eventrecommendation/',
                        '/api/v1/place/',
                        '/api/v1/place_full/',
                        '/api/v1/user/1/',
                        '/api/v1/event_featured/',
                        '/api/v1/event/'
                        ]
        # Get these values instead from the fixtures.
        params = '/api/v1/?' + self.encoded_params
        response = client.get(params)
        apis = json.loads(response.content)

        for list_endpoint in apis_to_test:
            url = list_endpoint + self.encoded_params
            api_response = client.get(url)
            print "URL    : ", url
            print "Content: ", api_response.content
            try:
                print "JSON:    ", json.loads(api_response.content), "\n"
            except:
                pass
            print "Endpoint:", list_endpoint
            print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

    # No need for this test since price isn't used by the UI
    def x_test_price(self):
        apis = ['/api/v1/price/']
        pass

    def test_category_api(self):
        api = '/api/v1/category/'
        self.assert200(api + self.encoded_params)

    def test_user_registration(self):
        api = '/api/v1/registration/'
        post_data = u'{"email": "some@example.com", "password1": "1234", "password2": "1234"}'
        client = Client()
        resp = client.post(api + self.encoded_params, data=post_data,
                           content_type='application/json')
        self.assertEqual(resp.status_code, 201)

    def test_event_recommendation(self):
        api = '/api/v1/eventrecommendation/'
        for loop in range(10):
            url = api + self.encoded_params
            self.assert200(url)

    def test_featured_event(self):
        api = '/api/v1/event_featured/'
        url = api + self.encoded_params
        self.assert200(url)

    def test_eventsummary(self):
        api = '/api/v1/eventsummary/'
        url = api + self.encoded_params
        self.assert200(url)

        for term in ['four', 'legend']:
            url = api + self.encoded_params + '&q=' + term
            self.assert200(url)

    #FAILING TEST - Investigate
    #Failed with a 410 o_O
    def test_event_full(self):
        # Todo: separate out each of these tests
        # Testing event description endpoint.
        api = '/api/v1/event_full/'
        for eventstr in self.events:
            url = api + eventstr + "/" + self.encoded_params
            self.assert200(url)

    #FAILING TEST - Investigate
    #Failed with a 401 (unauthorized)
    def test_event_action(self):
        api = '/api/v1/eventaction/'
        action = ['g', 'v', 'i', 'x']
        events = Event.objects.all()
        loops = len(events) * len(events)
        for loop in range(loops):
            event = Event.objects.order_by('?')[0]
            random_action = action[random.randrange(0,len(action))]
            post_data = u'{"action": "' + random_action
            post_data += '", "event": "/api/v1/event/' + str(event.id) + '/"}'
            resp = self.client.post(api + self.encoded_params,
                                    data=post_data,
                                    content_type='application/json')
            self.assertEqual(resp.status_code, 201)

    def test_simple_event_action(self):
        api = '/api/v1/eventaction/'
        event = Event.objects.get(id=1)
        action = 'g'
        post_data = u'{"action": "%s", "event": "/api/v1/event/%i/"}' % (action, event.id)
        resp = self.client.post(api + self.encoded_params,
                                data=post_data,
                                content_type='application/json')
        self.assertEqual(resp.status_code, 201)


    def assert200(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

