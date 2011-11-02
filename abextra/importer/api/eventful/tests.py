import os
import datetime
from dateutil.relativedelta import relativedelta
from dateutil import parser
import simplejson
from django.test import TestCase
from importer.models import Category, ExternalCategory, Source
from prices.models import Price
from places.models import City, Point, Place
from events.models import Event, Occurrence
from importer.api.eventful import conf, utils
from importer.api.eventful.adaptors import CityAdaptor, PointAdaptor, PlaceAdaptor
from importer.api.eventful.adaptors import OccurrenceAdaptor, EventAdaptor, CategoryAdaptor
from importer.api.eventful.adaptors import PriceAdaptor


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
        created, city = self.adaptor.parse(self.event_response)
        self.assertTrue(created, 'City object was not newly created')
        self.assertIsInstance(city, City, 'City type was expected')
        self.assertEqual(city.city, 'New York', 'Unexpected city value')
        self.assertEqual(city.state, 'NY', 'Unexpected state value')

    def test_adapt_new_invalid(self):
        created, city = self.adaptor.parse(self.invalid_response)
        self.assertFalse(created, 'City object created, despite invalid data')
        self.assertIsNone(city, 'City object returned, despite invalid data')

    def test_adapt_existing_valid(self):
        existing_city, _ = City.objects.get_or_create(city='New York', state='NY')
        created, city = self.adaptor.parse(self.event_response)
        self.assertFalse(created, 'City object created, despite existing match')
        self.assertEqual(existing_city, city, 'City object returned is not the existing match')


class PriceAdaptorTest(TestCase):
    fixtures = ('events',)

    def setUp(self):
        self.event_response = TestResourceConsumer.consume_response()
        self.invalid_response = TestResourceConsumer.consume_invalid_response()
        self.adaptor = PriceAdaptor()

    def test_adapt_new_valid(self):
        expanded_price = utils.expand_prices(self.event_response).next()
        occurrence = Occurrence.objects.all()[0]
        expanded_price['occurrence'] = occurrence.id

        created, price = self.adaptor.parse(expanded_price)
        self.assertTrue(created, 'Price object was not newly created')
        self.assertIsInstance(price, Price, 'Unexpected type of price object')
        self.assertEqual(12.00, price.quantity, 'Unexpected quantity value')
        self.assertEqual(u'dollars', price.units, 'Unexpected units value')

    def test_adapt_existing_valid(self):
        occurrence_obj = Occurrence.objects.all()[0]
        existing_price = Price(quantity=12.00, units='dollars', occurrence=occurrence_obj)
        existing_price.save()

        expanded_price = utils.expand_prices(self.event_response).next()
        expanded_price['occurrence'] = occurrence_obj.id

        created, price = self.adaptor.parse(expanded_price)
        self.assertFalse(created, 'Price object created despite existing match')
        self.assertEqual(existing_price, price, 'Price object returned is not the existing match')


    def test_adapt_new_invalid(self):
        expanded_price = list(utils.expand_prices(self.invalid_response)) or {}
        self.assertFalse(expanded_price)

        occurrence_obj = Occurrence.objects.all()[0]
        expanded_price['occurrence'] = occurrence_obj.id

        created, price = self.adaptor.parse(expanded_price)
        self.assertFalse(created, 'Price object created despite invalid data')
        self.assertIsNone(price, 'Price object returned despite invalid data')


class PointAdaptorTest(TestCase):
    fixtures = ['cities']

    def setUp(self):
        self.event_response = TestResourceConsumer.consume_response()
        self.invalid_response = TestResourceConsumer.consume_invalid_response()
        self.adaptor = PointAdaptor()

    def test_adapt_new_valid(self):
        created, point = self.adaptor.parse(self.event_response)
        self.assertTrue(created, 'Point object was not newly created')
        self.assertEqual(point.latitude, 40.7601, 'Unexpected latitude value')
        self.assertEqual(point.longitude, -73.9925, 'Unexpected longitude value')
        self.assertEqual(point.zip, u'10036', 'Unexpected zip value')
        self.assertEqual(point.address, u'349 W 46th Street between Eighth and Ninth Avenues', 'Unexpected address value')

    def test_adapt_new_invalid(self):
        created, point = self.adaptor.parse(self.invalid_response)
        self.assertFalse(created, 'Point object created despite invalid data')
        self.assertFalse(point, 'Point object created despite invalid data')

    def test_adapt_existing_valid(self):
        city_obj = City.objects.all()[0]
        existing_point = Point(latitude=40.7601, longitude=-73.9925, zip='10036',
                address='349 W 46th Street between Eighth and Ninth Avenues', city=city_obj)
        existing_point.save()

        created, point = self.adaptor.parse(self.event_response)
        self.assertFalse(created, 'Point object created despite existing match')
        self.assertEqual(existing_point, point, 'Point object returned is not the existing match')


class PlaceAdaptorTest(TestCase):
    fixtures = ['points']

    def setUp(self):
        self.event_response = TestResourceConsumer.consume_response()
        self.invalid_response = TestResourceConsumer.consume_invalid_response()
        self.adaptor = PlaceAdaptor()

    def test_adapt_new_valid(self):
        event_response = TestResourceConsumer.consume_response()
        adaptor = PlaceAdaptor()
        created, place = adaptor.parse(event_response)
        self.assertTrue(created, 'Place object was not newly created')
        self.assertEqual(u'Swing 46 Jazz and Supper Club', place.title, 'Unexpected place value')
        self.assertIsInstance(Point, place.point, 'Unexpected point type')

    def test_adapt_new_invalid(self):
        created, place = self.adaptor.parse(self.invalid_response)
        self.assertFalse(created, 'Place object created despite invalid data')
        self.assertFalse(place, 'Place object created despite invalid data')

    def test_adapt_existing_valid(self):
        point_obj = Point.objects.filter(address="349 W 46th Street between Eighth and Ninth Avenues")[0]
        existing_place = Place(title='Swing 46 Jazz and Supper Club', point=point_obj)
        existing_place.save()

        created, place = self.adaptor.parse(self.event_response)
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
        created, category = self.adaptor.parse(category_data[0])
        self.assertTrue(created, 'Category was not newly created')
        self.assertIsInstance(category, Category, 'Non Category object produced')
        self.assertEqual(u'Concerts & Tour Dates', category.name, 'Unexpected category name')
        self.assertEqual(u'music', category.xid, 'Unexpected category xid')

    def test_adapt_new_invalid(self):
        category_data = self.invalid_response['categories']['category']
        created, category = self.adaptor.parse(category_data[0])
        self.assertFalse(created, 'Category was created, despite invalid form')
        self.assertIsNone(category, 'Category object returned, despite invalid form')

    def test_adapt_existing_valid(self):
        eventful_source = Source.objects.filter(name='eventful')[0]
        existing_category = ExternalCategory(name='Concerts & Tour Dates',
                xid='music', source=eventful_source)
        existing_category.save()

        category_data = self.event_response['categories']['category']
        created, category = self.adaptor.parse(category_data[0])
        self.assertFalse(created)
        self.assertEqual(existing_category, category)

class OccurrenceAdaptorTest(TestCase):
    fixtures = ['auth', 'categories', 'sources', 'external_categories',
                'eventful_test_event', 'places', 'points']
    def setUp(self):
        self.event_response = TestResourceConsumer.consume_response()
        self.invalid_response = TestResourceConsumer.consume_invalid_response()
        self.adaptor = OccurrenceAdaptor()
        self.event_adaptor = EventAdaptor()

    def test_adapt_new_valid(self):

        event_obj = Event.objects.all()[0]
        occurrence_gen = self.event_adaptor.o2m_occurrences(self.event_response)
        first_occ = occurrence_gen.next()

        first_occ['event'] = event_obj.id

        created, occurrence = self.adaptor.parse(first_occ)
        self.assertIsInstance(occurrence.place, Place, 'Type of place object was unexpected')
        self.assertTrue(occurrence.event, Event, 'Type of event object was unexpected')
        self.assertEqual(occurrence.start_datetime, datetime.datetime(2011, 10,
            26, 20, 30), 'Unexpected start_datetime value')
        for occ in occurrence_gen:
            occ['event'] = event_obj.id
            created, occurrence = self.adaptor.parse(first_occ)
            self.assertTrue(created, 'Occurrence object was not newly created')

    def test_adapt_new_invalid(self):
        created, event = self.adaptor.parse(self.invalid_response)
        self.assertFalse(created)
        self.assertFalse(event)

    def test_adapt_existing_valid(self):
        event_obj = Event.objects.filter(title='The Stan Rubin Big Band--Dining and Swing Dancing in NYC!')[0]
        place_obj = Place.objects.filter(title='Swing 46 Jazz and Supper Club')[0]
        existing_occ = Occurrence(start_time=datetime.time(20, 30),
                start_date=datetime.date(2011, 10, 26), event=event_obj,
                place=place_obj)
        existing_occ.save()

        occurrence_gen = self.event_adaptor.o2m_occurrences(self.event_response)
        first_occ = occurrence_gen.next()
        first_occ['event'] = event_obj.id
        first_occ['place'] = place_obj.id

        created, occurrence = self.adaptor.parse(first_occ)
        self.assertFalse(created, 'Occurrence newly created despite existing match')
        self.assertEqual(existing_occ, occurrence, 'Occurrence object returned is not the existing match')


class EventAdaptorTest(TestCase):
    fixtures = ['auth', 'categories', 'sources', 'external_categories',
            'places', 'points', 'categories']

    def setUp(self):
        self.event_response = TestResourceConsumer.consume_response()
        self.invalid_response = TestResourceConsumer.consume_invalid_response()
        self.adaptor = EventAdaptor()


    def test_adapt_new_valid(self):

        created, occurrence = self.adaptor.parse(self.event_response)

        self.assertEqual(occurrence.xid, u'E0-001-015489401-9@2011102620', 'Unexpected xid value')
        self.assertEqual(occurrence.title, u'The Stan Rubin Big Band--Dining and Swing Dancing in NYC!', 'Unexpected title value')
        self.assertEqual(occurrence.description,
                         u'The Stan Rubin Orchestra plays favorites from the Big Band era for your dining and dancing pleasure!   Dance floor, full bar, Zagat-rated menu.',
                         'Unexpected description value')
        self.assertEqual(occurrence.url,
                         u'http://eventful.com/newyork_ny/events/stan-rubin-big-banddining-/E0-001-015489401-9@2011102620?utm_source=apis&utm_medium=apim&utm_campaign=apic',
                         'Unexpected url value')
        self.assertEqual(occurrence.concrete_category.title, u'Concerts', 'Unexpected concrete category title value')

    def test_adapt_new_invalid(self):
        # FIXME: rewrite base adaptor to swallow exceptions and return None if
        # fail_silent flag is set; then rewrite this test to reflect
        # expectations for that behavior 
        self.assertRaises(ValueError, self.adaptor.parse, self.invalid_response)

    def test_adapt_existing_valid(self):
        category_obj = Category.objects.filter(title='Concerts')[0]
        place_obj = Place.objects.filter(title='Swing 46 Jazz and Supper Club')[0]
        existing_event = Event(xid='E0-001-015489401-9@2011102620', title='The Stan Rubin Big Band--Dining and Swing Dancing in NYC!',
                description='The Stan Rubin Orchestra plays favorites from the Big Band era for your dining and dancing pleasure!   Dance floor, full bar, Zagat-rated menu.',
                concrete_category=category_obj)
        existing_event.save()

        created, occurrence = self.adaptor.parse(self.event_response)
        self.assertFalse(created, 'Event newly created despite existing match')
        self.assertEqual(existing_event, occurrence, 'Event object returned is not the existing match')

class EventfulParserPriceParsingTest(TestCase):
    # Parsing prices with units -- may get false positives, for now

    def test_multiple_prices_with_two_decimals_in_prose(self):
        price_data = {'free': None,
                      'price': '  Sign up by May 9th for a special discount. Early Registration 99.00 <br><br>  Sign up for the Pedestrian Consulting Mailing list following purchase to receive a 10% discount on the regular price course fee. See details below. Reduced Student Price -10% 250.00 <br><br>   Regular Student PriceOLD 199.00 <br><br>  Attend a meetup to find out how to become a member. Email info@pedestrianconsulting.com to find out how to become a member. Member Price 99.00 <br><br>   Non-Member Price 125.00 <br><br>  This is a 2 hour group hands on session. It is only available on Sept 5th Tuesday Sept 13th at 7 - 9 pm. The August 24th date is for the 3 hour class Sept 13th Website Bootcamp Lab 52.24 <br><br>  This is only held on Wednesday 8/24 at 7 - 9 pm. The other dates listed are for the labs August 24th 3 hour Class 77.87 <br><br>   October 24th Class 77.87 <br><br>\n'}
        parsed_prices = list(list(utils.expand_prices(price_data)))
        self.assertEqual([{'quantity': 52.24}, {'quantity': 77.87}, {'quantity': 99.0}, {'quantity': 125.0},
                          {'quantity': 199.0}, {'quantity': 250.0}], parsed_prices, 'Unexpected prices value')

    def test_single_price_with_two_decimals(self):
        price_data = {'free': None, 'price': '   RSVP 11.24 <br><br>\n'}
        parsed_prices = list(utils.expand_prices(price_data))
        self.assertEqual([{'quantity': 11.24}], parsed_prices, 'Unexpected prices value')

    def test_single_price_with_commas_two_decimals_and_no_units(self):
        price_data = {"price": "   General Registration 2,395.00 <br><br>   Early Bird 2,195.00 <br><br>\n",
                      "free": None}
        parsed_prices = list(utils.expand_prices(price_data))
        self.assertEqual([{'quantity': 2195.0}, {'quantity': 2395.0}],
                parsed_prices, 'Unexpected prices value')

    def test_single_price_with_units_in_USD(self):
        price_data = {"price": "5 - 5 USD ", "free": None}
        parsed_prices = list(utils.expand_prices(price_data))
        self.assertEqual([{'quantity': 5.0}], parsed_prices, 'Unexpected prices value')

    def test_single_price_with_units_in_dollar_sign(self):
        price_data = {"price": "$35", "free": "0"}
        parsed_prices = list(utils.expand_prices(price_data))
        self.assertEqual([{'quantity': 35.0}], parsed_prices, 'Unexpected prices value')

    def test_single_price_with_decimals_and_units_in_dollar_sign(self):
        price_data = {"price": "$10.00", "free": None}
        parsed_prices = list(utils.expand_prices(price_data))
        self.assertEqual([{'quantity': 10.0}], parsed_prices, 'Unexpected prices value')

    def test_multiple_prices_with_some_units_and_some_decimals(self):
        price_data = {"price": "  35% off reg $300 Saturdays 4:30-5:45 pm, 10/1-11/19 195.00 <br><br>\n", "free": None}
        parsed_prices = list(utils.expand_prices(price_data))
        self.assertEqual([{'quantity': 195.0}, {'quantity':300.0}],
                        parsed_prices, 'Unexpected prices value')

    # If 'free' field is not set, do not try to guess (for now)

    def test_free_in_price_field_and_not_in_free_field(self):
        price_data = {"price": "FREE", "free": None}
        parsed_prices = list(utils.expand_prices(price_data))
        self.assertEqual(parsed_prices, [], 'Unexpected prices value')


class EventfulParserDateParsingTest(TestCase):

    def test_single_occurrence_with_start_datetime(self):
        response = TestResourceConsumer.consume_recurrence_response()
        horizon_start, horizon_stop = response['__kwiqet']['horizon_start'], response['__kwiqet']['horizon_stop'] 
        start_datetimes, duration, is_all_day = utils.temporal_parser.occurrences(response)

        # test that event horizon clipping is working

        self.assertEqual(is_all_day, False)
        self.assertTrue(horizon_start < min(start_datetimes))
        self.assertTrue(max(start_datetimes) < horizon_stop)

        # now, test that distinct rrule and rdate parsing is working correctly:
        # try parsing from a year before creation date (set start_time and
        # horizon_start to a year prior): we should get rdates
        # that were otherwise clipped, and which are distinct from rrule
        # occurrences

        old_start_datetime = parser.parse(response['start_time'])
        new_start_datetime = old_start_datetime - relativedelta(years=1)
        response['__kwiqet']['horizon_start'], response['__kwiqet']['horizon_stop'] = horizon_start - relativedelta(years=1), horizon_stop + relativedelta(years=1)
        response['start_time'] = new_start_datetime.isoformat()
        start_datetimes, duration, is_all_day = utils.temporal_parser.occurrences(response)

        # check that first recurrence instance (original start datetime for the
        # event) is in resultant datetime set

        self.assertTrue(datetime.datetime(2011, 2, 19, 21, 0) in start_datetimes)

        # check that rdates are in resultant datetime set (they start at 14:30
        # instead of 21:00 like the other rrule recurrences)

        self.assertTrue(datetime.datetime(2011, 4, 10, 14, 30) in start_datetimes)

