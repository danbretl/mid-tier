import os
import datetime
from dateutil.relativedelta import relativedelta
from dateutil import parser
import simplejson
from django.test import TestCase
from importer.models import ExternalCategory, Source
from prices.models import Price
from places.models import City, Point, Place
from events.models import Event, Occurrence
from importer.api.eventful import conf, utils
from importer.api.eventful.adaptors import CityAdaptor, PointAdaptor, PlaceAdaptor
from importer.api.eventful.adaptors import OccurrenceAdaptor, EventAdaptor, CategoryAdaptor
from importer.api.eventful.adaptors import PriceAdaptor
from importer.api.eventful.utils import expand_prices, temporal_parser


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
        created, obj = self.adaptor.parse(self.event_response)
        self.assertTrue(created)
        self.assertEqual(obj.city, 'New York')
        self.assertEqual(obj.state, 'NY')

    def test_adapt_new_invalid(self):
        created, obj = self.adaptor.parse(self.invalid_response)
        self.assertFalse(created)
        self.assertFalse(obj)

    def test_adapt_existing_valid(self):
        existing_city = City(city='New York', state='NY')
        existing_city.save()
        created, obj = self.adaptor.parse(self.event_response)
        self.assertFalse(created)
        self.assertEqual(existing_city, obj)


class PriceAdaptorTest(TestCase):
    #FIXME should work with any existing valid occurrence fixture
    fixtures = ['occurrences']

    def setUp(self):
        self.event_response = TestResourceConsumer.consume_response()
        self.invalid_response = TestResourceConsumer.consume_invalid_response()
        self.adaptor = PriceAdaptor()

    def test_adapt_new_valid(self):
        expanded_price = utils.expand_prices(self.event_response).next()
        occurrence_obj = Occurrence.objects.all()[0]
        expanded_price['occurrence'] = occurrence_obj.id

        created, obj = self.adaptor.parse(expanded_price)
        self.assertTrue(created)
        self.assertEqual(obj.quantity, 12.00)
        self.assertEqual(obj.units, u'dollars')

    def test_adapt_existing_valid(self):
        occurrence_obj = Occurrence.objects.all()[0]
        existing_price = Price(quantity=12.00, units='dollars', occurrence=occurrence_obj)
        existing_price.save()

        expanded_price = utils.expand_prices(self.event_response).next()
        expanded_price['occurrence'] = occurrence_obj.id

        created, obj = self.adaptor.parse(expanded_price)
        self.assertFalse(created)
        self.assertEqual(existing_price, obj)


    def test_adapt_new_invalid(self):
        expanded_price = list(utils.expand_prices(self.invalid_response)) or {}
        self.assertFalse(expanded_price)

        occurrence_obj = Occurrence.objects.all()[0]
        expanded_price['occurrence'] = occurrence_obj.id

        created, obj = self.adaptor.parse(expanded_price)
        self.assertFalse(created)
        self.assertFalse(obj)


class PointAdaptorTest(TestCase):
    fixtures = ['cities']

    def setUp(self):
        self.event_response = TestResourceConsumer.consume_response()
        self.invalid_response = TestResourceConsumer.consume_invalid_response()
        self.adaptor = PointAdaptor()

    def test_adapt_new_valid(self):
        created, obj = self.adaptor.parse(self.event_response)
        self.assertTrue(created)
        self.assertEqual(obj.latitude, 40.7601)
        self.assertEqual(obj.longitude, -73.9925)
        self.assertEqual(obj.zip, u'10036')
        self.assertEqual(obj.address, u'349 W 46th Street between Eighth and Ninth Avenues')

    def test_adapt_new_invalid(self):
        created, obj = self.adaptor.parse(self.invalid_response)
        self.assertFalse(created)
        self.assertFalse(obj)

    def test_adapt_existing_valid(self):
        city_obj = City.objects.all()[0]
        existing_point = Point(latitude=40.7601, longitude=-73.9925, zip='10036',
                address='349 W 46th Street between Eighth and Ninth Avenues', city=city_obj)
        existing_point.save()

        created, obj = self.adaptor.parse(self.event_response)
        self.assertFalse(created)
        self.assertEqual(existing_point, obj)


class PlaceAdaptorTest(TestCase):
    fixtures = ['points']

    def setUp(self):
        self.event_response = TestResourceConsumer.consume_response()
        self.invalid_response = TestResourceConsumer.consume_invalid_response()
        self.adaptor = PlaceAdaptor()

    def test_adapt_new_valid(self):
        event_response = TestResourceConsumer.consume_response()
        adaptor = PlaceAdaptor()
        created, obj = adaptor.parse(event_response)
        self.assertTrue(created)
        self.assertEqual(obj.title, u'Swing 46 Jazz and Supper Club')
        self.assertTrue(obj.point)

    def test_adapt_new_invalid(self):
        created, obj = self.adaptor.parse(self.invalid_response)
        self.assertFalse(created)
        self.assertFalse(obj)

    def test_adapt_existing_valid(self):
        point_obj = Point.objects.all()[0]
        existing_place = Place(title='Swing 46 Jazz and Supper Club', point=point_obj)
        existing_place.save()

        created, obj = self.adaptor.parse(self.event_response)
        self.assertFalse(created)
        self.assertEqual(existing_place, obj)

class CategoryAdaptorTest(TestCase):
    fixtures = ['categories', 'sources']

    def setUp(self):
        self.event_response = TestResourceConsumer.consume_response()
        self.invalid_response = TestResourceConsumer.consume_invalid_response()
        self.adaptor = CategoryAdaptor()

    def test_adapt_new_valid(self):
        category_data = self.event_response['categories']['category']
        created, obj = self.adaptor.parse(category_data[0])
        self.assertEqual(obj.name, u'Concerts & Tour Dates')
        self.assertEqual(obj.xid, u'music')

    def test_adapt_new_invalid(self):
        category_data = self.invalid_response['categories']['category']
        created, obj = self.adaptor.parse(category_data[0])
        self.assertFalse(created)
        self.assertFalse(obj)

    def test_adapt_existing_valid(self):
        eventful_source = Source.objects.filter(name='eventful')[0]
        existing_category = ExternalCategory(name='Concerts & Tour Dates',
                xid='music', source=eventful_source)
        existing_category.save()

        category_data = self.event_response['categories']['category']
        created, obj = self.adaptor.parse(category_data[0])
        self.assertFalse(created)
        self.assertEqual(existing_category, obj)

class OccurrenceAdaptorTest(TestCase):
    fixtures = ['auth', 'categories', 'sources', 'external_categories',
                'eventful_test_event']
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

        created, obj = self.adaptor.parse(first_occ)
        self.assertTrue(obj.place)
        self.assertTrue(obj.event)
        self.assertEqual(obj.start_datetime, datetime.datetime(2011, 10, 26, 20, 30))
        for occ in occurrence_gen:
            occ['event'] = event_obj.id
            created, obj = self.adaptor.parse(first_occ)
            self.assertTrue(created)

    def test_adapt_new_invalid(self):
        created, obj = self.adaptor.parse(self.invalid_response)
        self.assertFalse(created)
        self.assertFalse(obj)

    def test_adapt_existing_valid(self):
        pass

class EventAdaptorTest(TestCase):
    fixtures = ['auth', 'categories', 'sources', 'external_categories']

    def setUp(self):
        self.event_response = TestResourceConsumer.consume_response()
        self.invalid_response = TestResourceConsumer.consume_invalid_response()
        self.adaptor = EventAdaptor()


    def test_adapt_new_valid(self):

        created, obj = self.adaptor.parse(self.event_response)

        self.assertEqual(obj.xid, u'E0-001-015489401-9@2011102620')
        self.assertEqual(obj.title, u'The Stan Rubin Big Band--Dining and Swing Dancing in NYC!')
        self.assertEqual(obj.description,
                         u'The Stan Rubin Orchestra plays favorites from the Big Band era for your dining and dancing pleasure!   Dance floor, full bar, Zagat-rated menu.')
        self.assertEqual(obj.url,
                         u'http://eventful.com/newyork_ny/events/stan-rubin-big-banddining-/E0-001-015489401-9@2011102620?utm_source=apis&utm_medium=apim&utm_campaign=apic')
        self.assertEqual(obj.concrete_category.title, u'Concerts')

        # check that we get multiple occurrences, check that they are being
        # correctly capped

    def test_adapt_new_invalid(self):
        created, obj = self.adaptor.parse(self.invalid_response)
        self.assertFalse(created)
        self.assertFalse(obj)

    def test_adapt_existing_valid(self):
        pass

class EventfulParserPriceParsingTest(TestCase):
    # Parsing prices with units -- may get false positives, for now

    def test_multiple_prices_with_two_decimals_in_prose(self):
        price_data = {'free': None,
                      'price': '  Sign up by May 9th for a special discount. Early Registration 99.00 <br><br>  Sign up for the Pedestrian Consulting Mailing list following purchase to receive a 10% discount on the regular price course fee. See details below. Reduced Student Price -10% 250.00 <br><br>   Regular Student PriceOLD 199.00 <br><br>  Attend a meetup to find out how to become a member. Email info@pedestrianconsulting.com to find out how to become a member. Member Price 99.00 <br><br>   Non-Member Price 125.00 <br><br>  This is a 2 hour group hands on session. It is only available on Sept 5th Tuesday Sept 13th at 7 - 9 pm. The August 24th date is for the 3 hour class Sept 13th Website Bootcamp Lab 52.24 <br><br>  This is only held on Wednesday 8/24 at 7 - 9 pm. The other dates listed are for the labs August 24th 3 hour Class 77.87 <br><br>   October 24th Class 77.87 <br><br>\n'}
        parsed_prices = list(list(expand_prices(price_data)))
        self.assertEqual(parsed_prices,
            [{'quantity': 52.24}, {'quantity': 77.87}, {'quantity': 99.0}, {'quantity': 125.0}, {'quantity': 199.0},
                    {'quantity': 250.0}])

    def test_single_price_with_two_decimals(self):
        price_data = {'free': None, 'price': '   RSVP 11.24 <br><br>\n'}
        parsed_prices = list(expand_prices(price_data))
        self.assertEqual(parsed_prices, [{'quantity': 11.24}])

    def test_single_price_with_commas_two_decimals_and_no_units(self):
        price_data = {"price": "   General Registration 2,395.00 <br><br>   Early Bird 2,195.00 <br><br>\n",
                      "free": None}
        parsed_prices = list(expand_prices(price_data))
        self.assertEqual(parsed_prices, [{'quantity': 2195.0}, {'quantity': 2395.0}])

    def test_single_price_with_units_in_USD(self):
        price_data = {"price": "5 - 5 USD ", "free": None}
        parsed_prices = list(expand_prices(price_data))
        self.assertEqual(parsed_prices, [{'quantity': 5.0}])

    def test_single_price_with_units_in_dollar_sign(self):
        price_data = {"price": "$35", "free": "0"}
        parsed_prices = list(expand_prices(price_data))
        self.assertEqual(parsed_prices, [{'quantity': 35.0}])

    def test_single_price_with_decimals_and_units_in_dollar_sign(self):
        price_data = {"price": "$10.00", "free": None}
        parsed_prices = list(expand_prices(price_data))
        self.assertEqual(parsed_prices, [{'quantity': 10.0}])

    def test_multiple_prices_with_some_units_and_some_decimals(self):
        price_data = {"price": "  35% off reg $300 Saturdays 4:30-5:45 pm, 10/1-11/19 195.00 <br><br>\n", "free": None}
        parsed_prices = list(expand_prices(price_data))
        self.assertEqual(parsed_prices, [{'quantity': 195.0}, {'quantity': 300.0}])

    # If 'free' field is not set, do not try to guess (for now)

    def test_free_in_price_field_and_not_in_free_field(self):
        price_data = {"price": "FREE", "free": None}
        parsed_prices = list(expand_prices(price_data))
        self.assertEqual(parsed_prices, [])


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

