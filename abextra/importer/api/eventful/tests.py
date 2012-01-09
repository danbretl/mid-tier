import os
import datetime
import HTMLParser
import dateutil.parser
from django.utils import simplejson as json
from dateutil.relativedelta import relativedelta
from django.contrib.gis import geos
from django.test import TestCase
from django_dynamic_fixture import F, G
from events.models import Event, Occurrence
from prices.models import Price
from places.models import City, Point, Place
from importer.models import Category, ExternalCategory, Source
from importer.api.eventful.client import API
from importer.api.eventful import conf, utils
from importer.api.eventful.adaptors import CityAdaptor, PointAdaptor, PlaceAdaptor
from importer.api.eventful.adaptors import OccurrenceAdaptor, EventAdaptor, CategoryAdaptor
from importer.api.eventful.adaptors import PriceAdaptor
from importer.api.eventful.paginator import EventfulPaginator
from accounts.models import User


class ImporterTestCase(TestCase):
    event_response, invalid_response = None, None
    point_address = u'349 W 46th Street between Eighth and Ninth Avenues'

    @staticmethod
    def parse_date(date_string):
        return datetime.datetime.strptime(date_string, '%Y-%m-%d').date()

    @staticmethod
    def parse_time(time_string):
        return datetime.datetime.strptime(time_string, '%H:%M').time()

    @staticmethod
    def resource_path(filename):
        resource_dir = os.path.join(os.path.dirname(__file__), 'test_resources')
        return os.path.join(resource_dir, filename)

    @classmethod
    def consume_response(cls, invalid=False):
        # convert filenames into qualified paths
        file_names = 'event', 'venue'
        file_paths = []
        for file_name in file_names:
            file_name = '.'.join((file_name, 'json'))
            if invalid:
                file_name = '_'.join(('invalid', file_name))
            file_paths.append(cls.resource_path(file_name))
        event, venue = file_paths

        # load up files and json load them
        with open(cls.resource_path(event), 'r') as f:
            event_response = json.load(f)
        with open(cls.resource_path(venue), 'r') as f:
            venue_response = json.load(f)

        horizon_start = datetime.datetime(2011, 10, 26, 20, 16)
        event_response['__kwiqet'] = {
            'venue_details': venue_response,
            'horizon_start': horizon_start,
            'horizon_stop': horizon_start + conf.IMPORT_EVENT_HORIZON,
            }
        return event_response

    @classmethod
    def consume_recurrence_response(cls):
        with open(cls.resource_path('recurrence_test_event.json'), 'r') as f:
            response = json.load(f)
        horizon_start = datetime.datetime(2011, 10, 26, 20, 16)
        response['__kwiqet'] = {
            'horizon_start': horizon_start,
            'horizon_stop': horizon_start + conf.IMPORT_EVENT_HORIZON,
            }
        return response

    @classmethod
    def setUpClass(cls):
        super(ImporterTestCase, cls).setUpClass()
        if not cls.event_response:
            cls.event_response = cls.consume_response()
        if not cls.invalid_response:
            cls.invalid_response = cls.consume_response(invalid=True)


class CityAdaptorTest(ImporterTestCase):
    @classmethod
    def setUpClass(cls):
        super(CityAdaptorTest, cls).setUpClass()
        cls.adaptor = CityAdaptor()

    def test_adapt_new_valid(self):
        created, city = self.adaptor.adapt(self.event_response)
        self.assertTrue(created, 'City object was not newly created')
        self.assertIsInstance(city, City, 'City type was expected')
        # check all attributes
        self.assertEqual('New York', city.city, 'Unexpected city value')
        self.assertEqual('NY', city.state, 'Unexpected state value')
        self.assertEqual('new-york-ny', city.slug, 'Unexpected slug value')

    def test_adapt_new_invalid(self):
        created, city = self.adaptor.adapt(self.invalid_response)
        self.assertFalse(created, 'City object created, despite invalid data')
        self.assertIsNone(city, 'City object returned, despite invalid data')

    def test_adapt_existing_valid(self):
        existing_city = G(City, city='New York', state='NY')
        created, city = self.adaptor.adapt(self.event_response)
        self.assertFalse(created, 'City object created, despite existing match')
        self.assertEqual(existing_city, city, 'City object returned is not the existing match')


class PriceAdaptorTest(ImporterTestCase):
    @classmethod
    def setUpClass(cls):
        super(PriceAdaptorTest, cls).setUpClass()
        cls.adaptor = PriceAdaptor()
        cls.quantities = {5.0, 12.0}

    def test_adapt_new_valid(self):
        occurrence = G(Occurrence, place=F(point=F(geometry=geos.Point(y=0, x=0))))
        prices = self.adaptor.adapt_m2o(self.event_response, occurrence=occurrence.id)
        for created, price in prices:
            self.assertTrue(created, 'Price object was not newly created')
            self.assertIsInstance(price, Price, 'Unexpected type of price object')
            self.assertIn(price.quantity, self.quantities, 'Unexpected quantity value')
            self.assertEqual(u'dollars', price.units, 'Unexpected units value')

    def test_adapt_existing_valid(self):
        occurrence = G(Occurrence, place=F(point=F(geometry=geos.Point(y=0, x=0))))
        existing_prices = {G(Price, occurrence=occurrence, quantity=quantity) for quantity in self.quantities}
        prices = self.adaptor.adapt_m2o(self.event_response, occurrence=occurrence.id)
        for created, price in prices:
            self.assertFalse(created, 'Price object created despite existing match')
            self.assertIn(price, existing_prices, 'Price object returned is not the existing match')


    def test_adapt_new_invalid(self):
        occurrence = G(Occurrence, place=F(point=F(geometry=geos.Point(y=40.7601, x=-73.9925))))

        created_prices = self.adaptor.adapt_m2o(self.invalid_response, occurrence=occurrence.id)
        self.assertTrue(all(not created for created, price in created_prices),
            'Price object created despite invalid data')
        self.assertTrue(all(price is None for created, price in created_prices),
            'Price object returned despite invalid data')


class PointAdaptorTest(ImporterTestCase):
    @classmethod
    def setUpClass(cls):
        super(PointAdaptorTest, cls).setUpClass()
        cls.adaptor = PointAdaptor()

    def test_adapt_new_valid(self):
        created, point = self.adaptor.adapt(self.event_response)
        self.assertTrue(created, 'Point object was not newly created')
        self.assertIsInstance(point, Point, 'Expected Point type')
        self.assertEqual(geos.Point(-73.9925, 40.7601), point.geometry, 'Unexpected geometry value')
        self.assertEqual(u'10036', point.zip, 'Unexpected zip value')
        self.assertEqual(self.point_address, point.address, 'Unexpected address value')
        self.assertIsInstance(point.city, City, 'Expected City type')

    def test_adapt_new_invalid(self):
        created, point = self.adaptor.adapt(self.invalid_response)
        self.assertFalse(created, 'Point object created despite invalid data')
        self.assertIsNone(point, 'Point object created despite invalid data')

    def test_adapt_existing_valid(self):
        # point uniqueness: address, city
        existing_point = G(Point, geometry=geos.Point(0, 0), address=self.point_address,
            city=City.objects.create(city='New York', state='NY')
        )
        created, point = self.adaptor.adapt(self.event_response)
        self.assertFalse(created, 'Point object created despite existing match')
        self.assertEqual(existing_point, point, 'Point object returned is not the existing match')


class PlaceAdaptorTest(ImporterTestCase):
    @classmethod
    def setUpClass(cls):
        super(PlaceAdaptorTest, cls).setUpClass()
        cls.adaptor = PlaceAdaptor()

    def test_adapt_new_valid(self):
        created, place = self.adaptor.adapt(self.event_response)
        self.assertTrue(created, 'Place object was not newly created')
        self.assertIsInstance(place, Place, 'Expected Place type')
        self.assertEqual(u'Swing 46 Jazz and Supper Club', place.title, 'Unexpected place value')
        self.assertIsInstance(place.point, Point, 'Expected Point type')

    def test_adapt_new_invalid(self):
        created, place = self.adaptor.adapt(self.invalid_response)
        self.assertFalse(created, 'Place object created despite invalid data')
        self.assertIsNone(place, 'Place object returned despite invalid data')

    def test_adapt_existing_valid(self):
        # place uniqueness: title, point
        existing_place = G(Place, title='Swing 46 Jazz and Supper Club', point=F(geometry=geos.Point(0, 0),
            address=self.point_address, city=City.objects.create(city='New York', state='NY')
        ))
        created, place = self.adaptor.adapt(self.event_response)
        self.assertFalse(created, 'Place object created despite existing match')
        self.assertEqual(existing_place, place, 'Place object returned is not the existing match')


class CategoryAdaptorTest(ImporterTestCase):
    fixtures = ['categories', 'sources']

    @classmethod
    def setUpClass(cls):
        super(CategoryAdaptorTest, cls).setUpClass()
        cls.adaptor = CategoryAdaptor()

    def test_adapt_new_valid(self):
        category_data = self.event_response['categories']['category']
        created, category = self.adaptor.adapt(category_data[0])
        self.assertTrue(created, 'Category was not newly created')
        self.assertIsInstance(category, ExternalCategory, 'Non Category object produced')
        self.assertEqual(u'Concerts & Tour Dates', category.name, 'Unexpected category name')
        self.assertEqual(u'music', category.xid, 'Unexpected category xid')

    def test_adapt_new_invalid(self):
        category_data = self.invalid_response['categories']['category']
        created, category = self.adaptor.adapt(category_data[0])
        self.assertFalse(created, 'Category was created, despite invalid form')
        self.assertIsNone(category, 'Category object returned, despite invalid form')

    def test_adapt_existing_valid(self):
        eventful_source = Source.objects.filter(name='eventful')[0]
        existing_category = G(ExternalCategory, name='Concerts & Tour Dates',
            xid='music', source=eventful_source)

        category_data = self.event_response['categories']['category']
        created, category = self.adaptor.adapt(category_data[0])
        self.assertFalse(created, 'Category object created despite existing match')
        self.assertEqual(existing_category, category, 'Category object returned is not the existing match')


class OccurrenceAdaptorTest(ImporterTestCase):
    fixtures = ['categories', 'sources']

    @classmethod
    def setUpClass(cls):
        super(OccurrenceAdaptorTest, cls).setUpClass()
        cls.adaptor = OccurrenceAdaptor()
        cls.expected_start_dates = map(cls.parse_date, '2011-10-26 2011-11-2 2011-11-9 2011-11-16 2011-11-23'.split())
        cls.expected_start_time = cls.parse_time('20:30')

    def test_adapt_new_valid(self):
        event = G(Event, xid='E0-001-042149604-1', title='Chromeo')
        occurrences = self.adaptor.adapt_m2o(self.event_response, event=event.id)
        self.assertEqual(len(occurrences), 5, 'Unexpected number of occurrences returned')
        for created, occurrence in occurrences:
            self.assertTrue(created, 'Not all occurrences were successfully created')
            self.assertIsInstance(occurrence, Occurrence, 'Occurrence type expected')
            self.assertIsInstance(occurrence.place, Place, 'Expected Place type')
            self.assertIsInstance(occurrence.event, Event, 'Expected Event type')
            self.assertIn(occurrence.start_date, self.expected_start_dates, 'Unexpected start date')
            self.assertEquals(occurrence.start_time, self.expected_start_time, 'Unexpected start times')

    def test_adapt_new_invalid(self):
        event = G(Event, xid='E0-001-042149604-1', title='Chromeo')
        self.assertRaises(ValueError, self.adaptor.adapt_m2o, self.invalid_response, event=event.id)

    def test_adapt_existing_valid(self):
        event, place = G(Event), G(Place, point=F(geometry=geos.Point(y=0, x=0)))
        existing_occurrences = {G(Occurrence, event=event, start_date=start_date,
            start_time=self.expected_start_time, place=place) for start_date in self.expected_start_dates
        }
        occurrences = self.adaptor.adapt_m2o(self.event_response, event=event.id, place=place.id)
        for created, occurrence in occurrences:
            self.assertFalse(created, 'Occurrence created despite existing match')
            self.assertIsInstance(occurrence, Occurrence, 'Occurrence type expected')
            self.assertIn(occurrence, existing_occurrences, 'Occurrence object returned is not the existing match')


class EventAdaptorTest(ImporterTestCase):
    fixtures = ['auth', 'categories', 'sources', 'external_categories']

    @classmethod
    def setUpClass(cls):
        super(EventAdaptorTest, cls).setUpClass()
        cls.adaptor = EventAdaptor()

    def test_adapt_new_valid(self):
        created, event = self.adaptor.adapt(self.event_response)
        self.assertTrue(created, 'Event object not newly created')
        self.assertIsInstance(event, Event, 'Event type unexpected')
        self.assertEqual(event.occurrences.count(), 5, 'No occurrences adapted')
        self.assertEqual(event.occurrences.all()[0].prices.count(), 2, 'No prices adapted')
        self.assertEqual(u'E0-001-015489401-9@2011102620', event.xid, 'Unexpected xid value')
        self.assertEqual(u'The Stan Rubin Big Band--Dining and Swing Dancing in NYC!', event.title,
            'Unexpected title value')
        self.assertEqual(u'The Stan Rubin Orchestra plays favorites from the Big Band era for your ' +
                         u'dining and dancing pleasure!   Dance floor, full bar, Zagat-rated menu.',
            event.description, 'Unexpected description value')
        self.assertEqual(u'http://eventful.com/newyork_ny/events/stan-rubin-big-banddining-/' +
                         u'E0-001-015489401-9@2011102620?utm_source=apis&utm_medium=apim&utm_campaign=apic',
            event.url, 'Unexpected url value')
        self.assertEqual(u'Concerts', event.concrete_category.title, 'Unexpected concrete category title value')

    def test_adapt_new_invalid(self):
        # FIXME: rewrite base adaptor to swallow exceptions and return None if
        # fail_silent flag is set; then rewrite this test to reflect
        # expectations for that behavior 
        self.assertRaises(ValueError, self.adaptor.adapt, self.invalid_response)

    def test_adapt_existing_valid(self):
        existing_event = G(Event, xid='E0-001-015489401-9@2011102620')
        created, event = self.adaptor.adapt(self.event_response)
        self.assertFalse(created, 'Event newly created despite existing match')
        self.assertEqual(existing_event, event, 'Event object returned is not the existing match')


class EventfulDateParserTest(ImporterTestCase):
    def test_single_occurrence_with_start_datetime(self):
        response = self.consume_recurrence_response()
        horizon_start, horizon_stop = response['__kwiqet']['horizon_start'], response['__kwiqet']['horizon_stop']
        start_datetimes, duration, is_all_day = utils.temporal_parser.occurrences(response)

        # test that event horizon clipping is working

        self.assertEqual(False, is_all_day, 'Unexpected is_all_day value')
        self.assertTrue(horizon_start < min(start_datetimes),
            'Datetime in occurrence set unexpectedly occurs before start of event horizon')
        self.assertTrue(max(start_datetimes) < horizon_stop,
            'Datetime in occurrence set unexpectedly occurs after end of event horizon')

        # now, test that distinct rrule and rdate parsing is working correctly:
        # try parsing from a year before creation date (set start_time and
        # horizon_start to a year prior): we should get rdates
        # that were otherwise clipped, and which are distinct from rrule
        # occurrences

        old_start_datetime = dateutil.parser.parse(response['start_time'])
        new_start_datetime = old_start_datetime - relativedelta(years=1)
        response['__kwiqet']['horizon_start'], response['__kwiqet']['horizon_stop'] = horizon_start - relativedelta(
            years=1), horizon_stop + relativedelta(years=1)
        response['start_time'] = new_start_datetime.isoformat()
        start_datetimes, duration, is_all_day = utils.temporal_parser.occurrences(response)

        # check that first recurrence instance (original start datetime for the
        # event) is in resultant datetime set

        self.assertTrue(datetime.datetime(2011, 2, 19, 21, 0) in start_datetimes,
            'First recurrence instance datetime is unexpectedly not a member of occurrence set')

        # check that rdates are in resultant datetime set (they start at 14:30
        # instead of 21:00 like the other rrule recurrences)

        self.assertTrue(datetime.datetime(2011, 4, 10, 14, 30) in
                        start_datetimes, 'First datetime in rdate set is unexpectedly not a member of occurrence set')


class ExternalCategoryFixtureTest(TestCase):
    fixtures = ['categories', 'sources', 'external_categories']

    def setUp(self):
        self.api = API()
        self.html_parser = HTMLParser.HTMLParser()
        self.eventful_sources = Source.objects.filter(name='eventful')

    def test_all_external_categories_imported(self):
        self.assertGreater(len(self.eventful_sources), 0, 'Unable to find Eventful source object')
        eventful_source = self.eventful_sources[0]

        resp = self.api.call('/categories/list')
        self.assertTrue(resp.get('category'))
        eventful_categories = resp.get('category')
        mapped_categories = []
        unmapped_categories = []

        for eventful_category in eventful_categories:
            xid, name = eventful_category['id'], self.html_parser.unescape(eventful_category['name'])
            mapped_category = ExternalCategory.objects.filter(xid=xid,
                source=eventful_source, name=name)
            if len(mapped_category) > 0:
                mapped_categories.extend(mapped_category)
            else:
                unmapped_categories.append(eventful_category)

        self.assertEqual([], unmapped_categories,
            'Unable to find external %s category mappings for: %s' %
            (eventful_source, ', '.join(map(lambda x: x['name'],
                unmapped_categories))))

    def test_all_external_categories_mapped(self):
        self.assertGreater(len(self.eventful_sources), 0, 'Unable to find Eventful source object')
        eventful_source = self.eventful_sources[0]
        external_categories = ExternalCategory.objects.filter(source=eventful_source)

        for external_category in external_categories:
            self.assertTrue(external_category.concrete_category,
                'External category for %s not mapped: %s' %
                (eventful_source.name, external_category.name))
            self.assertIsInstance(external_category.concrete_category,
                Category, 'Unexpected type of associated concrete category')


class EventfulPaginatorTest(ImporterTestCase):
    fixtures = ['categories', 'sources', 'external_categories', 'users']

    @classmethod
    def setUpClass(cls):
        super(EventfulPaginatorTest, cls).setUpClass()
        User.objects.create(username='importer')
        cls.args = dict(interactive=False, total_pages=1, start_page=1,
            silent_fail=False, consumer_kwargs={'trust': False, 'mock_api': True},
            client_kwargs={'make_dumps': False},
            query_kwargs={'query': '', 'sort_order': 'popularity', 'location': 'NYC', 'page_size': 1}
        )

    def test_silent_fail_off(self):
        with self.assertRaises(ValueError):
            self.paginator = EventfulPaginator(**self.args)
            self.paginator._import_page_events([self.invalid_response],
                self.args['interactive'], self.args['silent_fail'])

    def test_silent_fail_on(self):
        self.args['silent_fail'] = True
        self.paginator = EventfulPaginator(**self.args)
        self.paginator._import_page_events([self.invalid_response],
            self.args['interactive'], self.args['silent_fail'])
