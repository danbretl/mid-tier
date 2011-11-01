import os
import datetime
from dateutil.relativedelta import relativedelta
import simplejson
from django.test import TestCase
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


class CityAdaptorTest(TestCase):
    def test_city_adaptor(self):
        event_response = TestResourceConsumer.consume_response()
        adaptor = CityAdaptor()
        created, obj = adaptor.parse(event_response)
        self.assertTrue(created)
        self.assertEqual(obj.city, 'New York')
        self.assertEqual(obj.state, 'NY')

class PriceAdaptorTest(TestCase):
    fixtures = ['price_test_occurrence']

    def test_price_adaptor(self):
        event_response = TestResourceConsumer.consume_response()
        expanded_price = utils.expand_prices(event_response).next()
        occurrence_obj = Occurrence.objects.all()[0]
        expanded_price['occurrence'] = occurrence_obj.id

        adaptor = PriceAdaptor()
        created, obj = adaptor.parse(expanded_price)
        self.assertTrue(created)
        self.assertEqual(obj.quantity, 12.00)
        self.assertEqual(obj.units, u'dollars')


class PointAdaptorTest(TestCase):
    def test_point_adaptor(self):
        event_response = TestResourceConsumer.consume_response()
        adaptor = PointAdaptor()
        created, obj = adaptor.parse(event_response)
        self.assertTrue(created)
        self.assertEqual(obj.latitude, 40.7601)
        self.assertEqual(obj.longitude, -73.9925)
        self.assertEqual(obj.zip, u'10036')
        self.assertEqual(obj.address, u'349 W 46th Street between Eighth and Ninth Avenues')


class PlaceAdaptorTest(TestCase):
    def test_place_adaptor(self):
        event_response = TestResourceConsumer.consume_response()
        adaptor = PlaceAdaptor()
        created, obj = adaptor.parse(event_response)
        self.assertTrue(created)
        self.assertEqual(obj.title, u'Swing 46 Jazz and Supper Club')
        self.assertTrue(obj.point)


class CategoryAdaptorTest(TestCase):
    fixtures = ['categories', 'sources', 'external_categories']

    def test_category_adaptor(self):
        event_response = TestResourceConsumer.consume_response()
        category_data = event_response['categories']['category']
        adaptor = CategoryAdaptor()
        created, obj = adaptor.parse(category_data[0])
        self.assertEqual(obj.name, u'Concerts & Tour Dates')
        self.assertEqual(obj.xid, u'music')
        self.assertEqual(obj.concrete_category.title, u'Concerts')


class OccurrenceAdaptorTest(TestCase):
    fixtures = ['auth', 'categories', 'sources', 'external_categories',
                'eventful_test_event']

    def test_occurrence_adaptor(self):
        event_adaptor = EventAdaptor()
        adaptor = OccurrenceAdaptor()

        event_obj = Event.objects.all()[0]
        event_response = TestResourceConsumer.consume_response()
        occurrence_gen = event_adaptor.o2m_occurrences(event_response)
        first_occ = occurrence_gen.next()

        first_occ['event'] = event_obj.id

        created, obj = adaptor.parse(first_occ)
        self.assertTrue(obj.place)
        self.assertTrue(obj.event)
        self.assertEqual(obj.start_datetime, datetime.datetime(2011, 10, 26, 20, 30))
        for occ in occurrence_gen:
            occ['event'] = event_obj.id
            created, obj = adaptor.parse(first_occ)
            self.assertTrue(created)


class EventAdaptorTest(TestCase):
    fixtures = ['auth', 'categories', 'sources', 'external_categories']

    def test_event_adaptor(self):
        event_response = TestResourceConsumer.consume_response()
        adaptor = EventAdaptor()

        created, obj = adaptor.parse(event_response)

        self.assertEqual(obj.xid, u'E0-001-015489401-9@2011102620')
        self.assertEqual(obj.title, u'The Stan Rubin Big Band--Dining and Swing Dancing in NYC!')
        self.assertEqual(obj.description,
                         u'The Stan Rubin Orchestra plays favorites from the Big Band era for your dining and dancing pleasure!   Dance floor, full bar, Zagat-rated menu.')
        self.assertEqual(obj.url,
                         u'http://eventful.com/newyork_ny/events/stan-rubin-big-banddining-/E0-001-015489401-9@2011102620?utm_source=apis&utm_medium=apim&utm_campaign=apic')
        self.assertEqual(obj.concrete_category.title, u'Concerts')

        # check that we get multiple occurrences, check that they are being
        # correctly capped


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



        self.assertEqual(is_all_day, False)
        self.assertTrue(horizon_start < min(start_datetimes))
        self.assertTrue(max(start_datetimes) < horizon_stop)


