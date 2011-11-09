from itertools import repeat
import os
import datetime
import simplejson
from dateutil.relativedelta import relativedelta
import dateutil.parser
from django.contrib.gis import geos
from django.test import TestCase
from django_dynamic_fixture import get, DynamicFixture as F
from core.parsers import price_parser
from events.models import Event, Occurrence
from prices.models import Price
from places.models import City, Point, Place
from importer.models import Category, ExternalCategory, Source
from importer.api.eventful import conf, utils
from importer.api.eventful.adaptors import CityAdaptor, PointAdaptor, PlaceAdaptor
from importer.api.eventful.adaptors import OccurrenceAdaptor, EventAdaptor, CategoryAdaptor
from importer.api.eventful.adaptors import PriceAdaptor

_parse_date = lambda s: datetime.datetime.strptime(s, '%Y-%m-%d').date()
_parse_time = lambda s: datetime.datetime.strptime(s, '%H:%M').time()

class TestResourceConsumer(object):
    _RESOURCE_DIR = os.path.join(os.path.dirname(__file__), 'test_resources')

    @classmethod
    def consume_response(cls):
        event_filename, venue_filename = map(lambda f: os.path.join(cls._RESOURCE_DIR, f), 'event.json venue.json'.split())
        event_response = simplejson.load(open(event_filename, 'rb'))
        venue_response = simplejson.load(open(venue_filename, 'rb'))
        horizon_start = datetime.datetime(2011, 10, 26, 20, 16)
        event_response['__kwiqet'] = {
            'venue_details': venue_response,
            'horizon_start': horizon_start,
            'horizon_stop': horizon_start + conf.IMPORT_EVENT_HORIZON,
            }
        return event_response

    @classmethod
    def consume_recurrence_response(cls):
        filename = os.path.join(cls._RESOURCE_DIR, 'recurrence_test_event.json')
        horizon_start = datetime.datetime(2011, 10, 26, 20, 16)
        response = simplejson.load(open(filename, 'rb'))
        response['__kwiqet'] = {
            'horizon_start': horizon_start,
            'horizon_stop': horizon_start + conf.IMPORT_EVENT_HORIZON,
        }
        return response

    @classmethod
    def consume_invalid_response(cls):
        event_filename, venue_filename = map(lambda f: os.path.join(cls._RESOURCE_DIR, f), 'invalid_event.json invalid_venue.json'.split())
        event_response = simplejson.load(open(event_filename, 'rb'))
        venue_response = simplejson.load(open(venue_filename, 'rb'))
        horizon_start = datetime.datetime(2011, 10, 26, 20, 16)
        event_response['__kwiqet'] = {
            'venue_details': venue_response,
            'horizon_start': horizon_start,
            'horizon_stop': horizon_start + conf.IMPORT_EVENT_HORIZON,
        }
        return event_response


class CityAdaptorTest(TestCase):
    def setUp(self):
        self.event_response = TestResourceConsumer.consume_response()
        self.invalid_response = TestResourceConsumer.consume_invalid_response()
        self.adaptor = CityAdaptor()

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
        existing_city = get(City, city='New York', state='NY')
        created, city = self.adaptor.adapt(self.event_response)
        self.assertFalse(created, 'City object created, despite existing match')
        self.assertEqual(existing_city, city, 'City object returned is not the existing match')


class PriceAdaptorTest(TestCase):
    def setUp(self):
        self.event_response = TestResourceConsumer.consume_response()
        self.invalid_response = TestResourceConsumer.consume_invalid_response()
        self.adaptor = PriceAdaptor()
        self.expected_prices = [5.0, 12.0]

    def test_adapt_new_valid(self):
        occurrence = get(Occurrence, place=F(point=F(geometry=geos.Point(y=0, x=0))))

        created_prices = self.adaptor.adapt_m2o(self.event_response, occurrence=occurrence.id)
        self.assertTrue(all(created for created, price in created_prices), 'Price object was not newly created')
        self.assertTrue(all(isinstance(price, Price) for created, price in created_prices), 'Unexpected type of price object')
        self.assertEqual(self.expected_prices, [price.quantity for created, price in created_prices], 'Unexpected quantity value')
        self.assertTrue(all(u'dollars'==price.units for created, price in created_prices), 'Unexpected units value')

    def test_adapt_existing_valid(self):
        occurrence = get(Occurrence, place=F(point=F(geometry=geos.Point(y=0,x=0))))
        existing_prices = [get(Price, quantity=quantity, units='dollars', occurrence=occurrence) for quantity in self.expected_prices]

        created_prices = self.adaptor.adapt_m2o(self.event_response, occurrence=occurrence.id)

        self.assertTrue(all(not created for created, price in created_prices), 'Price object created despite existing match')
        self.assertTrue(all(price==existing_price for existing_price, (created, price) in zip (existing_prices, created_prices)),
            'Price object returned is not the existing match')


    def test_adapt_new_invalid(self):
        occurrence = get(Occurrence, place=F(point=F(geometry=geos.Point(y=40.7601, x=-73.9925))))

        created_prices = self.adaptor.adapt_m2o(self.invalid_response, occurrence=occurrence.id)
        self.assertTrue(all(not created for created, price in created_prices), 'Price object created despite invalid data')
        self.assertTrue(all(price==None for created, price in created_prices), 'Price object returned despite invalid data')


class PointAdaptorTest(TestCase):
    def setUp(self):
        self.event_response = TestResourceConsumer.consume_response()
        self.invalid_response = TestResourceConsumer.consume_invalid_response()
        self.adaptor = PointAdaptor()

    def test_adapt_new_valid(self):
        created, point = self.adaptor.adapt(self.event_response)
        self.assertTrue(created, 'Point object was not newly created')
        self.assertIsInstance(point, Point, 'Expected Point type')
        self.assertEqual(geos.Point(-73.9925, 40.7601), point.geometry, 'Unexpected geometry value')
        self.assertEqual(u'10036', point.zip, 'Unexpected zip value')
        self.assertEqual(u'349 W 46th Street between Eighth and Ninth Avenues', point.address, 'Unexpected address value')
        self.assertIsInstance(point.city, City, 'Expected City type')

    def test_adapt_new_invalid(self):
        created, point = self.adaptor.adapt(self.invalid_response)
        self.assertFalse(created, 'Point object created despite invalid data')
        self.assertIsNone(point, 'Point object created despite invalid data')

    def test_adapt_existing_valid(self):
        # point uniqueness: geometry, address
        existing_point = get(Point,
            geometry=geos.Point(y=40.7601, x=-73.9925),
            address='349 W 46th Street between Eighth and Ninth Avenues'
        )
        created, point = self.adaptor.adapt(self.event_response)
        self.assertFalse(created, 'Point object created despite existing match')
        self.assertEqual(existing_point, point, 'Point object returned is not the existing match')


class PlaceAdaptorTest(TestCase):
    def setUp(self):
        self.event_response = TestResourceConsumer.consume_response()
        self.invalid_response = TestResourceConsumer.consume_invalid_response()
        self.adaptor = PlaceAdaptor()

    def test_adapt_new_valid(self):
        event_response = TestResourceConsumer.consume_response()
        created, place = self.adaptor.adapt(event_response)
        self.assertTrue(created, 'Place object was not newly created')
        self.assertIsInstance(place, Place, 'Expected Place type')
        self.assertEqual(u'Swing 46 Jazz and Supper Club', place.title, 'Unexpected place value')
        self.assertIsInstance(place.point, Point, 'Expected Point type')

    def test_adapt_new_invalid(self):
        created, place = self.adaptor.adapt(self.invalid_response)
        self.assertFalse(created, 'Place object created despite invalid data')
        self.assertIsNone(place, 'Place object returned despite invalid data')

    def test_adapt_existing_valid(self):
        # place uniqueness: point, title
        existing_place = get(Place, title='Swing 46 Jazz and Supper Club', point=F(
            geometry=geos.Point(y=40.7601, x=-73.9925),
            address='349 W 46th Street between Eighth and Ninth Avenues'
        ))
        created, place = self.adaptor.adapt(self.event_response)
        self.assertFalse(created, 'Place object created despite existing match')
        self.assertEqual(existing_place, place, 'Place object returned is not the existing match')

class CategoryAdaptorTest(TestCase):
    fixtures = ['categories', 'sources']

    def setUp(self):
        self.event_response = TestResourceConsumer.consume_response()
        self.invalid_response = TestResourceConsumer.consume_invalid_response()
        self.adaptor = CategoryAdaptor()

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
        existing_category = get(ExternalCategory, name='Concerts & Tour Dates',
                xid='music', source=eventful_source)

        category_data = self.event_response['categories']['category']
        created, category = self.adaptor.adapt(category_data[0])
        self.assertFalse(created, 'Category object created despite existing match')
        self.assertEqual(existing_category, category, 'Category object returned is not the existing match')

class OccurrenceAdaptorTest(TestCase):
    fixtures = ['auth', 'categories', 'sources']

    def setUp(self):
        self.event_response = TestResourceConsumer.consume_response()
        self.invalid_response = TestResourceConsumer.consume_invalid_response()
        self.event_adaptor = EventAdaptor()
        self.adaptor = OccurrenceAdaptor()
        self.expected_start_dates = map(_parse_date, '2011-10-26 2011-11-2 2011-11-9 2011-11-16 2011-11-23'.split())
        self.expected_start_times = [_parse_time('20:30')] * len(self.expected_start_dates)

    def test_adapt_new_valid(self):

        event = get(Event, xid='E0-001-042149604-1', title='Chromeo')
        created_occurrences = list(self.adaptor.adapt_m2o(self.event_response, event=event.id))

        self.assertEqual(len(created_occurrences), 5, 'Unexpected number of occurrences returned')
        self.assertTrue(all(created for created, occurrences in created_occurrences),
                'Not all occurrences were successfully created')
        self.assertTrue(all(isinstance(occurrence, Occurrence) for created,
            occurrence in created_occurrences), 'Not all occurrences are of expected type') 
        self.assertTrue(all(isinstance(occurrence.place, Place) for created, occurrence in created_occurrences),
            'Expected Place type')
        self.assertTrue(all(isinstance(occurrence.event, Event) for created, occurrence in created_occurrences),
            'Expected Event type')
        self.assertEqual(self.expected_start_dates, [occurrence.start_date for created, occurrence in created_occurrences],
            'Unexpected values in start dates for occurrences')
        self.assertEqual(self.expected_start_times, [occurrence.start_time for created, occurrence in created_occurrences],
            'Unexpected values in start times for occurrences')

    def test_adapt_new_invalid(self):
        event = get(Event, xid='E0-001-042149604-1', title='Chromeo')
        self.assertRaises(ValueError, self.adaptor.adapt_m2o, self.invalid_response, event=event.id)

    def test_adapt_existing_valid(self):
        expected_start_date_iter = iter(self.expected_start_dates)
        expected_start_dates = lambda _: expected_start_date_iter.next()
        expected_start_time_iter = iter(self.expected_start_times)
        expected_start_times = lambda _: expected_start_time_iter.next()
        event, place = get(Event), get(Place, point=F(geometry=geos.Point(y=0, x=0)))
        existing_occs = get(Occurrence, event=event, start_date=expected_start_dates, start_time=expected_start_times,
            place=place, n=len(self.expected_start_dates)
        )

        created_occurrences = list(self.adaptor.adapt_m2o(self.event_response, event=event.id, place=place.id))
        self.assertTrue(all(not created for created, occurrence in created_occurrences),
                'Occurrence newly created despite existing match')
        self.assertTrue(all(existing_occ==occurrence for existing_occ, (created, occurrence) in zip(existing_occs, created_occurrences)),
                'Occurrence object returned is not the existing match')


class EventAdaptorTest(TestCase):
    fixtures = ['auth', 'categories', 'sources', 'external_categories']

    def setUp(self):
        self.event_response = TestResourceConsumer.consume_response()
        self.invalid_response = TestResourceConsumer.consume_invalid_response()
        self.adaptor = EventAdaptor()

    def test_adapt_new_valid(self):
        created, event = self.adaptor.adapt(self.event_response)
        self.assertTrue(created, 'Event object not newly created')
        self.assertIsInstance(event, Event, 'Event type unexpected')
        self.assertEqual(event.occurrences.count(), 5, 'No occurrences adapted')
        self.assertEqual(event.occurrences.all()[0].prices.count(), 2, 'No prices adapted')
        self.assertEqual(u'E0-001-015489401-9@2011102620', event.xid, 'Unexpected xid value')
        self.assertEqual(u'The Stan Rubin Big Band--Dining and Swing Dancing in NYC!', event.title, 'Unexpected title value')
        self.assertEqual(u'The Stan Rubin Orchestra plays favorites from the Big Band era for your dining and dancing pleasure!   Dance floor, full bar, Zagat-rated menu.',
                         event.description, 'Unexpected description value')
        self.assertEqual(u'http://eventful.com/newyork_ny/events/stan-rubin-big-banddining-/E0-001-015489401-9@2011102620?utm_source=apis&utm_medium=apim&utm_campaign=apic',
                         event.url, 'Unexpected url value')
        self.assertEqual(u'Concerts', event.concrete_category.title, 'Unexpected concrete category title value')

    def test_adapt_new_invalid(self):
        # FIXME: rewrite base adaptor to swallow exceptions and return None if
        # fail_silent flag is set; then rewrite this test to reflect
        # expectations for that behavior 
        self.assertRaises(ValueError, self.adaptor.adapt, self.invalid_response)

    def test_adapt_existing_valid(self):
        category_obj = get(Category, title='Concerts')
        existing_event = get(Event, xid='E0-001-015489401-9@2011102620', title='The Stan Rubin Big Band--Dining and Swing Dancing in NYC!',
                description='The Stan Rubin Orchestra plays favorites from the Big Band era for your dining and dancing pleasure!   Dance floor, full bar, Zagat-rated menu.',
                concrete_category=category_obj)

        created, event = self.adaptor.adapt(self.event_response)
        self.assertFalse(created, 'Event newly created despite existing match')
        self.assertEqual(existing_event, event, 'Event object returned is not the existing match')

class EventfulPriceParserTest(TestCase):
    # Parsing prices with units -- may get false positives, for now

    def test_multiple_prices_with_two_decimals_in_prose(self):
        price_data = {'free': None,
                      'price': '  Sign up by May 9th for a special discount. Early Registration 99.00 <br><br>  Sign up for the Pedestrian Consulting Mailing list following purchase to receive a 10% discount on the regular price course fee. See details below. Reduced Student Price -10% 250.00 <br><br>   Regular Student PriceOLD 199.00 <br><br>  Attend a meetup to find out how to become a member. Email info@pedestrianconsulting.com to find out how to become a member. Member Price 99.00 <br><br>   Non-Member Price 125.00 <br><br>  This is a 2 hour group hands on session. It is only available on Sept 5th Tuesday Sept 13th at 7 - 9 pm. The August 24th date is for the 3 hour class Sept 13th Website Bootcamp Lab 52.24 <br><br>  This is only held on Wednesday 8/24 at 7 - 9 pm. The other dates listed are for the labs August 24th 3 hour Class 77.87 <br><br>   October 24th Class 77.87 <br><br>\n'}
        adapted_prices = (price_parser.parse(price_data['price']))
        self.assertEqual([52.24, 77.87, 99.0, 125.0, 199.0, 250.0], sorted(set(adapted_prices)), 'Unexpected prices value')

    def test_single_price_with_two_decimals(self):
        price_data = {'free': None, 'price': '   RSVP 11.24 <br><br>\n'}
        adapted_prices = (price_parser.parse(price_data['price']))
        self.assertEqual([11.24], sorted(set(adapted_prices)), 'Unexpected prices value')

    def test_single_price_with_commas_two_decimals_and_no_units(self):
        price_data = {"price": "   General Registration 2,395.00 <br><br>   Early Bird 2,195.00 <br><br>\n",
                      "free": None}
        adapted_prices = (price_parser.parse(price_data['price']))
        self.assertEqual([2195.0, 2395.0], sorted(set(adapted_prices)), 'Unexpected prices value')

    def test_single_price_with_units_in_USD(self):
        price_data = {"price": "5 - 5 USD ", "free": None}
        adapted_prices = (price_parser.parse(price_data['price']))
        self.assertEqual([5.0], sorted(set(adapted_prices)), 'Unexpected prices value')

    def test_single_price_with_units_in_dollar_sign(self):
        price_data = {"price": "$35", "free": "0"}
        adapted_prices = (price_parser.parse(price_data['price']))
        self.assertEqual([35.0], sorted(set(adapted_prices)), 'Unexpected prices value')

    def test_single_price_with_decimals_and_units_in_dollar_sign(self):
        price_data = {"price": "$10.00", "free": None}
        adapted_prices = (price_parser.parse(price_data['price']))
        self.assertEqual([10.0], sorted(set(adapted_prices)), 'Unexpected prices value')

    def test_multiple_prices_with_some_units_and_some_decimals(self):
        price_data = {"price": "  35% off reg $300 Saturdays 4:30-5:45 pm, 10/1-11/19 195.00 <br><br>\n", "free": None}
        adapted_prices = (price_parser.parse(price_data['price']))
        self.assertEqual([195.0, 300.0], sorted(set(adapted_prices)), 'Unexpected prices value')
    
class EventfulDateParserTest(TestCase):

    def test_single_occurrence_with_start_datetime(self):
        response = TestResourceConsumer.consume_recurrence_response()
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
        response['__kwiqet']['horizon_start'], response['__kwiqet']['horizon_stop'] = horizon_start - relativedelta(years=1), horizon_stop + relativedelta(years=1)
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

