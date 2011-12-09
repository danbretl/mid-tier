import datetime
from django.conf import settings
from dateutil.relativedelta import relativedelta
from django.utils import simplejson as json
import logging
import urllib
import base64

from django.contrib.auth.models import User
from django.contrib.gis import geos
from django.test import TestCase
from django.test.client import Client
from django_dynamic_fixture import get, DynamicFixture as F
from test_utils import build_uri, try_json_loads
from test_utils import CategoryFilterOptions, DateFilterOptions
from test_utils import PriceFilterOptions, TimeFilterOptions
from test_utils import BaseFilterOptions

from accounts.models import UserProfile
from api.models import Consumer
from behavior.models import EventAction, EventActionAggregate
from events.models import Category, Event, EventSummary, Occurrence
from prices.models import Price
from behavior.resources import EventActionResource, EventActionAggregateResource
from events.resources import EventRecommendationResource
from events.resources import CategoryResource, FeaturedEventResource, EventSummaryResource
from events.resources import OccurrenceResource, OccurrenceFullResource, EventResource, EventFullResource
from accounts.resources import UserResource, PasswordResetResource
from api.resources import ApiKeyResource, UserProfileResource
import livesettings

TEST_LOGGER = logging.getLogger('api.test')

class APIResourceTestCase(TestCase):
    fixtures = ['auth', 'consumers']
    resource = None

    def setUp(self):
        self.uri = build_uri(self.resource._meta.resource_name)
        consumer = Consumer.objects.get(id=1)
        self.auth_params = {'consumer_key': consumer.key,
                                            'consumer_secret': consumer.secret,
                                            'udid': '6AAD4638-7E07-5A5C-A676-3D16E4AFFAF3',
        }
        self.client = Client()

    def assertResponseCode(self, resp, expected_code):
        """Assert that a response has an expected status code"""
        self.assertEqual(expected_code, resp.status_code, 'Expected %s, received %s on a %s to %s' % (
            expected_code, resp.status_code,
            resp.request['REQUEST_METHOD'], resp.request['PATH_INFO']
        ))

    def assertResponseMetaList(self, resp, expected_count):
        resp_dict = try_json_loads(resp.content)
        self.assertIsNotNone(resp_dict, 'Malformed response')
        self.assertIsNotNone(resp_dict.get('objects'), 'Malformed objects field from response')
        self.assertIsNotNone(resp_dict.get('meta'), 'Malformed meta field from response')
        meta_field = resp_dict['meta']
        self.assertEqual(expected_count, meta_field['total_count'],
                'Incorrect count of objects in meta field of response')
        self.assertEqual(expected_count, len(resp_dict.get('objects')),
                'Incorrect count of objects in response')


class CategoryResourceTest(APIResourceTestCase):
    resource = CategoryResource

    def test_list_get(self):
        parent_category = get(Category, parent=None)
        categories = get(Category, parent=parent_category, n=2)
        categories.append(parent_category)
        resp = self.client.get(self.uri, data=self.auth_params)
        self.assertResponseCode(resp, 200)
        self.assertResponseMetaList(resp, len(categories))


class OccurrenceResourceTest(APIResourceTestCase):
    resource = OccurrenceResource

    def test_list_get_past(self):
        get(Occurrence, place=F(point=F(geometry=geos.Point(y=0, x=0))))
        resp = self.client.get(self.uri, data=self.auth_params)
        self.assertResponseCode(resp, 200)
        self.assertResponseMetaList(resp, 0)

    def test_list_get_future(self):
        get(Occurrence, start_date = datetime.datetime.now().date() + datetime.timedelta(days=10),
                place=F(point=F(geometry=geos.Point(y=0, x=0))))
        resp = self.client.get(self.uri, data=self.auth_params)
        self.assertResponseCode(resp, 200)
        self.assertResponseMetaList(resp, 1)

    def test_detail_get_past(self):
        occ = get(Occurrence, place=F(point=F(geometry=geos.Point(y=0, x=0))))
        uri = self.resource().get_resource_uri(occ)
        resp = self.client.get(uri, data=self.auth_params)
        resp_dict = try_json_loads(resp.content)
        self.assertIsNone(resp_dict, 'Returned unexpected existing occurrence')
        self.assertResponseCode(resp, 410)

    def test_detail_get_future(self):
        occ = get(Occurrence, start_date = datetime.datetime.now().date() + datetime.timedelta(days=30),
                place=F(point=F(geometry=geos.Point(y=0, x=0))))
        uri = self.resource().get_resource_uri(occ)
        resp = self.client.get(uri, data=self.auth_params)
        resp_dict = try_json_loads(resp.content)
        self.assertIsNotNone(resp_dict, 'Malformed response')
        self.assertResponseCode(resp, 200)
        self.assertEqual(uri, resp_dict['resource_uri'],
                'Unexpected resource uri in response')
        event_field = resp_dict.get('event')
        self.assertIsInstance(event_field, basestring,
                'Did not find expected reference to associated event URI in event field')
        place_field = resp_dict.get('place')
        self.assertIsInstance(place_field, basestring,
                'Did not find expected reference to associated place URI in place field')


class OccurrenceFullResourceTest(OccurrenceResourceTest):
    resource = OccurrenceFullResource

    def test_detail_get_future(self):
        occ = get(Occurrence, start_date = datetime.datetime.now().date() + datetime.timedelta(days=30),
                place=F(point=F(geometry=geos.Point(y=0, x=0))))
        uri = self.resource().get_resource_uri(occ)
        resp = self.client.get(uri, data=self.auth_params)
        resp_dict = try_json_loads(resp.content)
        self.assertIsNotNone(resp_dict, 'Malformed response')
        self.assertResponseCode(resp, 200)
        self.assertEqual(uri, resp_dict['resource_uri'],
                'Unexpected resource uri in response')

        event_field = resp_dict.get('event')
        self.assertIsInstance(event_field, basestring, 'Did not find expected reference to associated event URI')
        place_field = resp_dict.get('place')
        self.assertIsInstance(place_field, dict, 'Full occurrence does not have place dict')
        point_field = place_field.get('point')
        self.assertIsInstance(point_field, dict, 'Full occurrence dict does not have point dict')
        city_field = point_field.get('city')
        self.assertIsInstance(city_field, dict, 'Full occurrence dict does not have city dict')


class EventSummaryResourceTest(APIResourceTestCase):
    resource = EventSummaryResource

    def test_list_get(self):
        event_summaries = get(EventSummary, n=2)
        resp = self.client.get(self.uri, data=self.auth_params)
        self.assertResponseCode(resp, 200)
        self.assertResponseMetaList(resp, len(event_summaries))


class BaseEventResourceTest(APIResourceTestCase):
    fixtures = ['auth', 'consumers', 'categories']
    resource = EventResource

    def setUp(self):
        super(BaseEventResourceTest, self).setUp()

    @staticmethod
    def make_event_fixture():
        event = get(Event, concrete_category=Category.objects.get(slug='music'),
                secret_key='f'*10)
        occurrence = get(Occurrence, start_date=datetime.date(2063, 1, 1),
            place=F(point=F(geometry=geos.Point(x=0,y=0))),
            event=event)
        get(Price, occurrence=occurrence)
        event.save()
        return event


class BaseEventSummaryTest(BaseEventResourceTest):
    resource = EventSummaryResource
    filter_options_class = BaseFilterOptions

    def setUp(self):
        super(BaseEventResourceTest, self).setUp()
        if not hasattr(self, 'filter_options'):
            self.filter_options = self.filter_options_class()

class EventSummaryCompositeFilterTest(BaseEventSummaryTest):
    filter_options_class_mappings = {'filter_options': BaseFilterOptions}

    def setUp(self):
        super(EventSummaryCompositeFilterTest, self).setUp()
        for attribute_name, filter_options_class in self.filter_options_class_mappings.iteritems():
            if not hasattr(self, attribute_name):
                setattr(self, attribute_name, filter_options_class())


class BaseEventRecommendationTest(BaseEventSummaryTest):
    resource = EventRecommendationResource

class EventRecommendationCompositeFilterTest(EventSummaryCompositeFilterTest):
    resource = EventRecommendationResource

class CategoryFilterMixin:

    @staticmethod
    def _set_event_category(event, category_slug):
        filter_options = CategoryFilterOptions()
        event.concrete_category = filter_options.category_by_slug[category_slug]
        event.save()
        return event

    @classmethod
    def mutate_fixture_matched(cls, event, category_slug='music'):
        return cls._set_event_category(event, category_slug)

    @classmethod
    def mutate_fixture_unmatched(cls, event, category_slug='nightlife'):
        return cls._set_event_category(event, category_slug)

    def test_category_filters_music(self):
        matched_event = self.__class__.mutate_fixture_matched(BaseEventSummaryTest.make_event_fixture())
        self.__class__.mutate_fixture_unmatched(BaseEventSummaryTest.make_event_fixture())

        query_params = dict(**self.auth_params)
        query_params.update(**self.filter_options.music)
        resp = self.client.get(self.uri, data=query_params)

        self.assertResponseCode(resp, 200)
        self.assertResponseMetaList(resp, 1)

        json_resp = try_json_loads(resp.content)
        first_search_result_uri = json_resp['objects'][0]['resource_uri']
        expected_first_uri = self.resource().get_resource_uri(matched_event)
        self.assertEqual(expected_first_uri, first_search_result_uri,
                'Unexpected event in results for category filter')


class EventSummaryCategoryFilterTest(BaseEventSummaryTest, CategoryFilterMixin):
    filter_options_class = CategoryFilterOptions


class EventRecommendationCategoryFilterTest(BaseEventRecommendationTest, CategoryFilterMixin):
    filter_options_class = CategoryFilterOptions


class PriceFilterMixin:

    @staticmethod
    def _set_event_price(event, quantity):
        occurrence = event.occurrences.all()[0]
        price = occurrence.prices.all()[0]
        price.quantity = quantity
        price.save()
        occurrence.save()
        event.save()
        return event

    @classmethod
    def mutate_fixture_matched(cls, event, quantity=10):
        return cls._set_event_price(event, quantity)

    @classmethod
    def mutate_fixture_unmatched(cls, event, quantity=30):
        return cls._set_event_price(event, quantity)

    def test_price_filters_under_twenty(self):
        matched_event = self.__class__.mutate_fixture_matched(BaseEventSummaryTest.make_event_fixture())
        self.__class__.mutate_fixture_unmatched(BaseEventSummaryTest.make_event_fixture())

        query_params = dict(**self.auth_params)
        query_params.update(**self.filter_options.under_twenty)
        resp = self.client.get(self.uri, data=query_params)

        self.assertResponseCode(resp, 200)
        self.assertResponseMetaList(resp, 1)

        json_resp = try_json_loads(resp.content)
        first_search_result_uri = json_resp['objects'][0]['resource_uri']
        expected_first_uri = self.resource().get_resource_uri(matched_event)
        self.assertEqual(expected_first_uri, first_search_result_uri,
                'Unexpected event in results for under price filter')


class EventSummaryPriceFilterTest(BaseEventSummaryTest, PriceFilterMixin):
    filter_options_class = PriceFilterOptions


class EventRecommendationPriceFilterTest(BaseEventRecommendationTest, PriceFilterMixin):
    filter_options_class = PriceFilterOptions


class DateFilterMixin:

    @staticmethod
    def _set_event_date(event, start_date):
        occurrence = event.occurrences.all()[0]
        occurrence.start_date = start_date
        occurrence.save()
        event.save()
        return event

    @classmethod
    def mutate_fixture_matched(cls, event, date):
        return cls._set_event_date(event, date)

    @classmethod
    def mutate_fixture_unmatched(cls, event, date):
        return cls._set_event_date(event, date)

    def test_date_filters_this_weekend(self):
        now = datetime.datetime.now()
        matched_event = self.__class__.mutate_fixture_matched(BaseEventSummaryTest.make_event_fixture(),
                (now + relativedelta(weekday=5)).date())
        self.__class__.mutate_fixture_unmatched(BaseEventSummaryTest.make_event_fixture(),
            (now + datetime.timedelta(days=30)).date())

        query_params = dict(**self.auth_params)
        query_params.update(**self.filter_options.this_weekend)
        resp = self.client.get(self.uri, data=query_params)

        self.assertResponseCode(resp, 200)
        self.assertResponseMetaList(resp, 1)

        json_resp = try_json_loads(resp.content)
        first_search_result_uri = json_resp['objects'][0]['resource_uri']
        expected_first_uri = self.resource().get_resource_uri(matched_event)
        self.assertEqual(expected_first_uri, first_search_result_uri,
                'Unexpected event in results for this weekend date filter')

    def test_date_filters_next_seven_days(self):
        now = datetime.datetime.now()
        matched_event = self.__class__.mutate_fixture_matched(BaseEventSummaryTest.make_event_fixture(),
                (now + relativedelta(days=4)).date())
        self.__class__.mutate_fixture_unmatched(BaseEventSummaryTest.make_event_fixture(),
            (now + datetime.timedelta(days=10)).date())

        query_params = dict(**self.auth_params)
        query_params.update(**self.filter_options.next_seven_days)
        resp = self.client.get(self.uri, data=query_params)

        self.assertResponseCode(resp, 200)
        self.assertResponseMetaList(resp, 1)

        json_resp = try_json_loads(resp.content)
        first_search_result_uri = json_resp['objects'][0]['resource_uri']
        expected_first_uri = self.resource().get_resource_uri(matched_event)
        self.assertEqual(expected_first_uri, first_search_result_uri,
                'Unexpected event in results for next 7 days date filter')


class DateFilterTest(DateFilterMixin, BaseEventSummaryTest):
    filter_options_class = DateFilterOptions

class TimeFilterMixin:

    @staticmethod
    def _set_event_time(event, start_time):
        occurrence = event.occurrences.all()[0]
        occurrence.start_time = start_time
        occurrence.save()
        event.save()
        return event

    @classmethod
    def mutate_fixture_matched(cls, event, time):
        return cls._set_event_time(event, time)

    @classmethod
    def mutate_fixture_unmatched(cls, event, time):
        return cls._set_event_time(event, time)

    def test_time_filters_morning(self):
        matched_event = self.__class__.mutate_fixture_matched(BaseEventSummaryTest.make_event_fixture(),
                datetime.time(10, 0))
        self.__class__.mutate_fixture_unmatched(BaseEventSummaryTest.make_event_fixture(),
            datetime.time(20, 0))

        query_params = dict(**self.auth_params)
        query_params.update(**self.filter_options.morning)
        resp = self.client.get(self.uri, data=query_params)

        self.assertResponseCode(resp, 200)
        self.assertResponseMetaList(resp, 1)

        json_resp = try_json_loads(resp.content)
        first_search_result_uri = json_resp['objects'][0]['resource_uri']
        expected_first_uri = self.resource().get_resource_uri(matched_event)
        self.assertEqual(expected_first_uri, first_search_result_uri,
                'Unexpected event in results for morning time filter')


class TimeFilterTest(TimeFilterMixin, BaseEventSummaryTest):
    filter_options_class = TimeFilterOptions


class PriceCategoryFilterMixin:

    def test_price_category_filters(self):
        matched_event = CategoryFilterMixin.mutate_fixture_matched(BaseEventSummaryTest.make_event_fixture())
        unmatched_event = CategoryFilterMixin.mutate_fixture_unmatched(BaseEventSummaryTest.make_event_fixture())
        PriceFilterMixin.mutate_fixture_matched(matched_event)
        PriceFilterMixin.mutate_fixture_unmatched(unmatched_event)

        query_params = dict(self.category_filter_options.music, **self.auth_params)
        query_params.update(self.price_filter_options.under_twenty)
        resp = self.client.get(self.uri, data=query_params)

        self.assertResponseCode(resp, 200)
        self.assertResponseMetaList(resp, 1)

        json_resp = try_json_loads(resp.content)
        first_search_result_uri = json_resp['objects'][0]['resource_uri']
        expected_first_uri = self.resource().get_resource_uri(matched_event)
        self.assertEqual(expected_first_uri, first_search_result_uri,
                'Unexpected event in results for price and category filter combination')


class EventSummaryPriceCategoryFilterTest(PriceCategoryFilterMixin, EventSummaryCompositeFilterTest):
    filter_options_class_mappings = {'category_filter_options': CategoryFilterOptions,
            'price_filter_options': PriceFilterOptions}

class EventRecommendationPriceCategoryFilterTest(PriceCategoryFilterMixin, EventRecommendationCompositeFilterTest):
    filter_options_class_mappings = {'category_filter_options': CategoryFilterOptions,
            'price_filter_options': PriceFilterOptions}

class TimeCategoryFilterMixin:

    def test_time_category_filters(self):
        matched_event = CategoryFilterMixin.mutate_fixture_matched(BaseEventSummaryTest.make_event_fixture())
        unmatched_event = CategoryFilterMixin.mutate_fixture_unmatched(BaseEventSummaryTest.make_event_fixture())
        TimeFilterMixin.mutate_fixture_matched(matched_event, datetime.time(19,0))
        TimeFilterMixin.mutate_fixture_unmatched(unmatched_event, datetime.time(22,0))

        query_params = dict(self.category_filter_options.music, **self.auth_params)
        query_params.update(self.time_filter_options.evening)
        resp = self.client.get(self.uri, data=query_params)

        self.assertResponseCode(resp, 200)
        self.assertResponseMetaList(resp, 1)

        json_resp = try_json_loads(resp.content)
        first_search_result_uri = json_resp['objects'][0]['resource_uri']
        expected_first_uri = self.resource().get_resource_uri(matched_event)
        self.assertEqual(expected_first_uri, first_search_result_uri,
                'Unexpected event in results for time and category filter combination')


class EventSummaryTimeCategoryFilterTest(TimeCategoryFilterMixin, EventSummaryCompositeFilterTest):
    filter_options_class_mappings = {'category_filter_options': CategoryFilterOptions,
            'time_filter_options': TimeFilterOptions}


class EventRecommendationTimeCategoryFilterTest(TimeCategoryFilterMixin, EventRecommendationCompositeFilterTest):
    filter_options_class_mappings = {'category_filter_options': CategoryFilterOptions,
            'time_filter_options': TimeFilterOptions}


class DateCategoryFilterMixin:

    def test_date_this_weekend_category_filters(self):
        now = datetime.datetime.now()
        matched_event = CategoryFilterMixin.mutate_fixture_matched(BaseEventSummaryTest.make_event_fixture())
        unmatched_event = CategoryFilterMixin.mutate_fixture_unmatched(BaseEventSummaryTest.make_event_fixture())
        DateFilterMixin.mutate_fixture_matched(matched_event, (now + relativedelta(weekday=5)).date())
        DateFilterMixin.mutate_fixture_unmatched(unmatched_event, (now + relativedelta(days=30)).date())

        query_params = dict(self.category_filter_options.music, **self.auth_params)
        query_params.update(self.date_filter_options.this_weekend)
        resp = self.client.get(self.uri, data=query_params)

        self.assertResponseCode(resp, 200)
        self.assertResponseMetaList(resp, 1)

        json_resp = try_json_loads(resp.content)
        first_search_result_uri = json_resp['objects'][0]['resource_uri']
        expected_first_uri = self.resource().get_resource_uri(matched_event)
        self.assertEqual(expected_first_uri, first_search_result_uri,
                'Unexpected event in results for date (next weekend) and category filter combination')


    def test_date_next_seven_days_category_filters(self):

        now = datetime.datetime.now()
        matched_event = CategoryFilterMixin.mutate_fixture_matched(BaseEventSummaryTest.make_event_fixture())
        unmatched_event = CategoryFilterMixin.mutate_fixture_unmatched(BaseEventSummaryTest.make_event_fixture())
        DateFilterMixin.mutate_fixture_matched(matched_event, (now + relativedelta(days=4)).date())
        DateFilterMixin.mutate_fixture_unmatched(unmatched_event, (now + datetime.timedelta(days=10)).date())


        query_params = dict(self.category_filter_options.music, **self.auth_params)
        query_params.update(self.date_filter_options.next_seven_days)
        resp = self.client.get(self.uri, data=query_params)

        self.assertResponseCode(resp, 200)
        self.assertResponseMetaList(resp, 1)

        json_resp = try_json_loads(resp.content)
        first_search_result_uri = json_resp['objects'][0]['resource_uri']
        expected_first_uri = self.resource().get_resource_uri(matched_event)
        self.assertEqual(expected_first_uri, first_search_result_uri,
                'Unexpected event in results for date (next 7 days) and category filter combination')


class EventSummaryDateCategoryFilterTest(DateCategoryFilterMixin, EventSummaryCompositeFilterTest):
    filter_options_class_mappings = {'category_filter_options': CategoryFilterOptions,
            'date_filter_options': DateFilterOptions}


class EventRecommendationDateCategoryFilterTest(DateCategoryFilterMixin, EventRecommendationCompositeFilterTest):
    filter_options_class_mappings = {'category_filter_options': CategoryFilterOptions,
            'date_filter_options': DateFilterOptions}


class FullTextSearchTest(BaseEventSummaryTest):

    def test_fts_title_simple(self):
        keyword = 'guitar'
        title_with_kw = 'Title including %s' % keyword

        matched_event = BaseEventSummaryTest.make_event_fixture()
        matched_event.title=title_with_kw
        matched_event.save()

        BaseEventSummaryTest.make_event_fixture()

        query_params = dict(q=keyword, **self.auth_params)
        resp = self.client.get(self.uri, data=query_params)

        self.assertResponseCode(resp, 200)
        # should only get the single relevent event in response
        self.assertResponseMetaList(resp, 1)

        json_resp = try_json_loads(resp.content)
        first_search_result_uri = json_resp['objects'][0]['resource_uri']
        expected_first_uri = self.resource().get_resource_uri(matched_event)
        self.assertEqual(expected_first_uri, first_search_result_uri,
                'Unexpected search result')

    def test_fts_description_simple(self):
        keyword = 'guitar'
        description_with_kw = 'Description including %s' % keyword

        matched_event = BaseEventSummaryTest.make_event_fixture()
        matched_event.description = description_with_kw
        matched_event.save()

        BaseEventSummaryTest.make_event_fixture()

        query_params = dict(q=keyword, **self.auth_params)
        resp = self.client.get(self.uri, data=query_params)

        self.assertResponseCode(resp, 200)
        self.assertResponseMetaList(resp, 1)

        json_resp = try_json_loads(resp.content)
        first_search_result_uri = json_resp['objects'][0]['resource_uri']
        expected_first_uri = self.resource().get_resource_uri(matched_event)
        self.assertEqual(expected_first_uri, first_search_result_uri,
                'Unexpected search result')

    def test_fts_title_description_ranking(self):
        keyword = 'guitar'
        title_with_kw = 'Title including %s' % keyword
        description_with_kw = 'Description including %s' % keyword

        events = []
        # create & save events in reverse order to expected search order
        for title, description in reversed(((title_with_kw, description_with_kw,), (title_with_kw, ''), ('', description_with_kw),)):
            event = (BaseEventSummaryTest.make_event_fixture())
            event.title = title
            event.description = description
            event.save()
            events.insert(0, event)

        BaseEventSummaryTest.make_event_fixture()

        query_params = dict(q=keyword, **self.auth_params)
        resp = self.client.get(self.uri, data=query_params)

        self.assertResponseCode(resp, 200)
        self.assertResponseMetaList(resp, len(events))

        json_resp = try_json_loads(resp.content)
        for ix, search_result in enumerate(json_resp['objects']):
            search_result_uri = search_result['resource_uri']
            expected_uri = self.resource().get_resource_uri(events[ix])
            self.assertEqual(expected_uri, search_result_uri,
            '''Unexpected search ranking for summary with title %s and
            description %s''' % (events[ix].title, events[ix].description))


class EventResourceTest(BaseEventResourceTest):

    def test_detail_get(self):
        event = BaseEventSummaryTest.make_event_fixture()

        uri = self.resource().get_resource_uri(event)
        resp = self.client.get(uri, data=self.auth_params)
        resp_dict = try_json_loads(resp.content)
        self.assertIsNotNone(resp_dict, 'Malformed response')
        self.assertResponseCode(resp, 200)
        self.assertEqual(uri, resp_dict['resource_uri'],
                'Unexpected resource uri in response')

        occurrences_field = resp_dict.get('occurrences')
        self.assertIsInstance(occurrences_field[0], basestring,
                'Did not find expected reference to occurrence URI')


class EventFullResourceTest(BaseEventResourceTest):
    resource = EventFullResource

    def test_detail_get(self):
        event = BaseEventSummaryTest.make_event_fixture()

        uri = self.resource().get_resource_uri(event)
        resp = self.client.get(uri, data=self.auth_params)
        resp_dict = try_json_loads(resp.content)
        self.assertIsNotNone(resp_dict, 'Malformed response')
        self.assertResponseCode(resp, 200)
        self.assertEqual(uri, resp_dict['resource_uri'],
                'Unexpected resource uri in response')

        occurrences_field = resp_dict.get('occurrences')
        self.assertIsInstance(occurrences_field[0], dict,
                'Did not find expected occurrence child dictionary')


class EventRecommendationResourceTest(BaseEventRecommendationTest):

    def test_list_get(self):
        events = []
        for ix in range(2):
            event = BaseEventSummaryTest.make_event_fixture()
            events.append(event)
        resp = self.client.get(self.uri, data=self.auth_params)
        resp_dict = try_json_loads(resp.content)
        self.assertIsNotNone(resp_dict, 'Malformed response')
        self.assertResponseCode(resp, 200)
        self.assertResponseMetaList(resp, len(events))

        event_titles = set(e.title for e in events)
        produced_event_titles = set(e['title'] for e in resp_dict['objects'])

        self.assertEqual(event_titles, produced_event_titles,
                'Unexpected initial recommended events set')


class FeaturedEventResourceTest(BaseEventResourceTest):
    resource = FeaturedEventResource

    def test_list_get(self):
        events = []
        for ix in range(2):
            events.append(BaseEventResourceTest.make_event_fixture())
        featured_event = livesettings.config_get('EVENTS','FEATURED_EVENT_ID')

        events[0].id = featured_event.value
        events[0].save()

        featured_event.update(events[0].id)
        resp = self.client.get(self.uri, data=self.auth_params)
        self.assertResponseCode(resp, 200)
        self.assertResponseMetaList(resp, 1)

class EventActionAggregateResourceTest(APIResourceTestCase):
    resource = EventActionAggregateResource

    def test_list_delete(self):
        get(EventActionAggregate)
        resp = self.client.delete(self.uri, data=self.auth_params)
        self.assertResponseCode(resp, 204)

class EventActionResourceTest(APIResourceTestCase):
    resource = EventActionResource

    def test_event_actions_persisted(self):
        events = get(Event,n=2)
        event_uri = self.resource().get_resource_uri(events[0])
        encoded_auth_params = '?' + urllib.urlencode(self.auth_params)
        actions = ('g', 'v', 'i', 'x')
        for action in actions:
            json_params = json.dumps(dict(action=action, event=event_uri))
            action_resp = self.client.post(self.uri + encoded_auth_params,
                    json_params, content_type='application/json')
            self.assertEqual(201, action_resp.status_code,
                    'Unexpected HTTP status code %s for event action' % action_resp.status_code)
            event_action_aggregate = EventActionAggregate.objects.all()[0]
            action_count = EventAction.objects.filter(action=action.upper()).count()
            self.assertEqual(action_count, getattr(event_action_aggregate, action),
                    'Incorrect aggregate count of %s actions' % action.upper())
            for other_action in (oa for oa in actions if not oa == action):
                self.assertEqual(0, getattr(event_action_aggregate, other_action),
                        'Unexpected nonzero count of %s actions given that %s was chosen' %
                        (other_action.upper(), action.upper()))

    def test_list_delete(self):
        get(Event)
        resp = self.client.delete(self.uri, data=self.auth_params)
        self.assertResponseCode(resp, 204)


class UserResourceTest(APIResourceTestCase):
    resource = UserResource
    valid_email, invalid_email = 'someone@example.com', 'invalid'
    first_name, last_name = 'babygot', 'back'
    password = 'p0ssword'

    def test_detail_post(self):
        encoded_auth_params = '?' + urllib.urlencode(self.auth_params)
        json_params = json.dumps({'email': self.valid_email,
                                  'password1': self.password, 'password2': self.password,
                                  'first_name': self.first_name, 'last_name': self.last_name})
        resp = self.client.post(self.uri + encoded_auth_params, json_params, content_type='application/json')
        self.assertResponseCode(resp, 201)
        users = User.objects.filter(email=self.valid_email)
        self.assertEquals(1, len(users), 'Unexpected amount of users')
        user = users[0]
        self.assertEquals(resp.content, user.api_key.key, 'Unexpected api key for user')
        self.assertTrue(user.check_password(self.password), 'Unexpected password')
        self.assertEquals(self.valid_email, user.email, 'Unexpected email address')
        self.assertEquals(self.last_name, user.last_name, 'Unexpected last name')


    def test_registration_response_user_does_not_exist(self):
        email = 'someone@example.com'

        encoded_auth_params = '?' + urllib.urlencode(self.auth_params)
        json_params = json.dumps({'email': email})
        # test that registration with email address not yet associated with
        # account doesn't yield 'this email address is already in use' error
        resp = self.client.post(self.uri + encoded_auth_params, json_params, content_type='application/json')
        self.assertResponseCode(resp, 400)
        json_resp = try_json_loads(resp.content)
        resp_email_field = json_resp.get('email')
        self.assertIsNone(resp_email_field, 'Account unexpectedly exists')

    def test_registration_invalid_email(self):
        encoded_auth_params = '?' + urllib.urlencode(self.auth_params)
        json_params = json.dumps({'email': self.invalid_email, 'password1':
            self.password, 'password1': self.password, 'password2': self.password})
        resp = self.client.post(self.uri + encoded_auth_params, json_params, content_type='application/json')
        self.assertResponseCode(resp, 400)


class ApiKeyResourceTest(APIResourceTestCase):
    resource = ApiKeyResource
    username = 'username'
    password = 'password'
    email = 'user@name.com'

    def test_list_get(self):
        new_user = User.objects.create_user(self.username, self.email, self.password)
        auth_header = 'Basic %s' % base64.b64encode('%s:%s' % (self.email,
            self.password))
        resp = self.client.get(self.uri, data=self.auth_params,
                HTTP_AUTHORIZATION=auth_header)
        self.assertResponseCode(resp, 200)
        resp_dict = try_json_loads(resp.content)
        self.assertIsNotNone(resp_dict, 'Malformed response')
        api_key_obj = resp_dict['objects'][0]
        self.assertEqual(new_user.api_key.key, api_key_obj['key'],
                'Unexpected key %s returned for user %s in response, expecting %s' %
                (api_key_obj['key'], new_user.username, new_user.api_key.key))

    def test_login_response_user_does_not_exist(self):
        auth_header = 'Basic %s' % base64.b64encode('%s:%s' % ('a', 'a'))
        resp = self.client.get(self.uri, data=self.auth_params,
                HTTP_AUTHORIZATION=auth_header)
        TEST_LOGGER.debug('For testing login response where user does not exist:')
        TEST_LOGGER.debug('Response content: %s' % resp.content)
        TEST_LOGGER.debug('Response status code: %s' % resp.status_code)

    def test_login_response_user_exists_wrong_password(self):
        User.objects.create_user(self.username, self.email, self.password)

        auth_header = 'Basic %s' % base64.b64encode('%s:%s' % (self.email, 'a'))
        resp = self.client.get(self.uri, data=self.auth_params,
                HTTP_AUTHORIZATION=auth_header)
        TEST_LOGGER.debug('For testing login response where user exists, wrong password given:')
        TEST_LOGGER.debug('Response content: %s' % resp.content)
        TEST_LOGGER.debug('Response status code: %s' % resp.status_code)

class UserProfileResourceTest(APIResourceTestCase):
    resource = UserProfileResource
    password = 'moo'

    def test_list_get(self):
        user_profile = get(UserProfile)
        user_profile.user.set_password(self.password)
        user_profile.user.save()
       
        api_auth_params = dict(api_key=user_profile.user.api_key.key,
                **self.auth_params)
        resp = self.client.get(self.uri, data=api_auth_params)

        self.assertResponseCode(resp, 200)
        self.assertResponseMetaList(resp, 1)
        resp_dict = try_json_loads(resp.content)
        user_dict = resp_dict['objects'][0]

        user_uri = self.resource().get_resource_uri(user_profile)
        self.assertEquals(user_uri, user_dict['resource_uri'], '''Unexpected URI for
                user''')
        self.assertEquals(user_profile.user.first_name, user_dict['first_name'], '''Unexpected
                first name for user''')
        self.assertEquals(user_profile.user.last_name, user_dict['last_name'], '''Unexpected
                last name for user''')


class PasswordResetResourceTest(APIResourceTestCase):
    resource = PasswordResetResource

    def test_list_post(self):
        username = 'username'
        password = 'password'
        email = 'user@name.com'
        User.objects.create_user(username, email, password)
        json_params = json.dumps({"email": email, "username": username,
            "password": password})
        encoded_auth_params = '?' + urllib.urlencode(self.auth_params)
        resp = self.client.post(self.uri + encoded_auth_params, json_params, content_type='application/json')
        self.assertResponseCode(resp, 201)
