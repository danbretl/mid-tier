import datetime
from django.test import TestCase
from django.conf import settings
from events.models import Event
# from importer.consumer import ScrapeFeedConsumer
from importer.api.eventful.consumer import EventfulApiConsumer
from importer.api.eventful.adaptors import CityAdaptor, PointAdaptor, PlaceAdaptor
from importer.api.eventful.adaptors import OccurrenceAdaptor, EventAdaptor, CategoryAdaptor
from importer.api.eventful.adaptors import PriceAdaptor, EventAdaptor
from importer.api.eventful.utils import expand_prices, temporal_parser
from importer.api.eventful.paginator import EventfulPaginator

# class ExternalCategoryParserTest(TestCase):
#     fixtures = ['sources'] # ,'external_categories']
#     # consumer = ScrapeFeedConsumer()
#     parser = ExternalCategoryAdaptor()
#
#     def test_parse(self):
#         for category in self.consumer.categories:
#             self.parser.parse(category)
#
# class CityParserTest(TestCase):
#     # consumer = ScrapeFeedConsumer()
#     parser = CityAdaptor()
#
#     def test_parse(self):
#         for location in self.consumer.locations:
#             self.parser.parse(location)
#
# class PointParserTest(TestCase):
#     # consumer = ScrapeFeedConsumer()
#     parser = PointAdaptor()
#
#     def test_parse(self):
#         for location in self.consumer.locations:
#             self.parser.parse(location)
#
# class PlaceParserTest(TestCase):
#     # consumer = ScrapeFeedConsumer()
#     parser = PlaceAdaptor()
#
#     def test_parse(self):
#         for location in self.consumer.locations:
#             self.parser.parse(location)
#
# class PriceParserTest(TestCase):
#     fixtures = ['events']
#     # consumer = ScrapeFeedConsumer()
#     parser = PriceAdaptor()
#
#     def test_parse(self):
#         for price in self.consumer.prices:
#             price['occurrence'] = 1
#             self.parser.parse(price)
#
# class OccurrenceParserTest(TestCase):
#     fixtures = ['events']
#     # consumer = ScrapeFeedConsumer()
#     parser = OccurrenceAdaptor()
#
#     def test_parse(self):
#         for occurrence in self.consumer.occurrences:
#             self.parser.parse(occurrence)

# class EventParserTest(TestCase):
    # fixtures = ['auth', 'categories', 'sources', 'external_categories']

    # def setUp(self):
        # self.consumer = ScrapeFeedConsumer()
        # self.parser = EventAdaptor()

    # def test_parse(self):
        # for event in self.consumer.events():
            # self.parser.parse(event)

class EventfulParserTest(TestCase):
    fixtures = ['auth', 'categories', 'sources', 'external_categories']

    def setUp(self):
        # self.consumer = SimpleApiConsumer()
        # self.parser = EventAdaptor()
        self.importer = EventfulPaginator(page_size=100, total_pages=2)

    def test_parse(self):
        events = self.importer.import_events()
        # for event in events:
            # try:
                # event_obj = self.parser.parse(event)
            # except ValueError as parse_err:
                # self.logger.warn("Encountered exception while parsing:")
                # self.logger.warn(parse_err.args)

class EventfulParserMockAPIAndDumpTest(TestCase):
    fixtures = ['auth', 'categories', 'sources', 'external_categories']

    def setUp(self):
        # self.consumer = SimpleApiConsumer()
        # self.parser = EventAdaptor()
        self.importer = EventfulPaginator(page_size=10, current_page=1,
                total_pages=3, mock_api=False, make_dumps=True)

    def test_parse(self):
        imported_events = self.importer.import_events()
        created_events = []
        existing_events = []
        for was_created, event_id in imported_events:
            if was_created and event_id:
                created_events.append(event_id)
            else:
                existing_events.append(event_id)
        assert(created_events)

        for e_id in created_events:
                e_obj = Event.objects.filter(id=e_id)
                if e_obj:
                    e_obj.delete()

        self.importer = EventfulPaginator(page_size=10, current_page=1,
                total_pages=3, mock_api=True, make_dumps=False)
        imported_events = self.importer.import_events()
        created_events = []
        existing_events = []
        for was_created, event_id in imported_events:
            if was_created and event_id:
                created_events.append(event_id)
            else:
                existing_events.append(event_id)
        assert(created_events)

        # for event in events:
            # try:
                # event_obj = self.parser.parse(event)
            # except ValueError as parse_err:
                # self.logger.warn("Encountered exception while parsing:")
                # self.logger.warn(parse_err.args)


class EventfulParserPriceParsingTest(TestCase):
    # Parsing prices with units -- may get false positives, for now

    def test_multiple_prices_with_two_decimals_in_prose(self):
        price_data = {'free': None,
            'price': '  Sign up by May 9th for a special discount. Early Registration 99.00 <br><br>  Sign up for the Pedestrian Consulting Mailing list following purchase to receive a 10% discount on the regular price course fee. See details below. Reduced Student Price -10% 250.00 <br><br>   Regular Student PriceOLD 199.00 <br><br>  Attend a meetup to find out how to become a member. Email info@pedestrianconsulting.com to find out how to become a member. Member Price 99.00 <br><br>   Non-Member Price 125.00 <br><br>  This is a 2 hour group hands on session. It is only available on Sept 5th Tuesday Sept 13th at 7 - 9 pm. The August 24th date is for the 3 hour class Sept 13th Website Bootcamp Lab 52.24 <br><br>  This is only held on Wednesday 8/24 at 7 - 9 pm. The other dates listed are for the labs August 24th 3 hour Class 77.87 <br><br>   October 24th Class 77.87 <br><br>\n'}
        self.assertEqual(expand_prices(price_data), [{'quantity': '52.24'}, {'quantity': '77.87'}, {'quantity': '99.0'}, {'quantity': '125.0'}, {'quantity': '199.0'}, {'quantity': '250.0'}])

    def test_single_price_with_two_decimals(self):
        price_data = {'free': None, 'price': '   RSVP 11.24 <br><br>\n'}
        self.assertEqual(expand_prices(price_data), [{'quantity': '11.24'}])

    def test_single_price_with_commas_two_decimals_and_no_units(self):
        price_data = {"price": "   General Registration 2,395.00 <br><br>   Early Bird 2,195.00 <br><br>\n",
            "free": None}
        self.assertEqual(expand_prices(price_data), [{'quantity': '2195.0'}, {'quantity': '2395.0'}])

    def test_single_price_with_units_in_USD(self):
        price_data = {"price": "5 - 5 USD ", "free": None}
        self.assertEqual(expand_prices(price_data), [{'quantity': '5.0'}])

    def test_single_price_with_units_in_dollar_sign(self):
        price_data = {"price": "$35","free": "0"}
        self.assertEqual(expand_prices(price_data), [{'quantity': '35.0'}])

    def test_single_price_with_decimals_and_units_in_dollar_sign(self):
        price_data = {"price": "$10.00","free": None}
        self.assertEqual(expand_prices(price_data), [{'quantity': '10.0'}])

    def test_multiple_prices_with_some_units_and_some_decimals(self):
        price_data =  {"price": "  35% off reg $300 Saturdays 4:30-5:45 pm, 10/1-11/19 195.00 <br><br>\n","free": None}
        self.assertEqual(expand_prices(price_data), [{'quantity': '195.0'}, {'quantity': '300.0'}])

    # If 'free' field is not set, do not try to guess (for now)

    def test_free_in_price_field_and_not_in_free_field(self):
        price_data = {"price": "FREE","free": None}
        self.assertEqual(expand_prices(price_data), [])


class EventfulParserDateParsingTest(TestCase):
    # FIXME: Parsing occurrences without getting first instance for now; this is not
    # really correct though

    # fixtures = ['auth', 'categories', 'sources', 'external_categories']

    def test_single_occurrence_with_start_datetime(self):
        occurrence_data = {"start_time": "2011-10-13 18:00:00"}
        start_time = temporal_parser._parse_datetime(occurrence_data['start_time'])
        self.assertEqual(start_time, datetime.datetime(2011, 10, 13, 18, 0))
        occurrence_set = temporal_parser._recurrence_set(occurrence_data)
        self.assertEqual(occurrence_set, set())

    def test_single_occurrence_with_start_and_end_datetime(self):
        occurrence_data = {"start_time": "2011-10-13 19:00:00","stop_time": "2011-10-13 21:00:00"}
        start_time = temporal_parser._parse_datetime(occurrence_data['start_time'])
        self.assertEqual(start_time, datetime.datetime(2011, 10, 13, 19, 0))
        stop_time = temporal_parser._parse_datetime(occurrence_data['stop_time'])
        self.assertEqual(stop_time, datetime.datetime(2011, 10, 13, 21, 0))

    def test_multiple_occurrences_with_start_datetime(self):
        occurrence_data = { "recurrence": { "rrules": {"rrule": "FREQ=DAILY;BYHOUR=13;BYMINUTE=00;UNTIL=20120109T235959"},
                    "exrules": None, "rdates": None, "description": "daily until January 9, 2012",
                    "exdates": None }, "start_time": "2011-10-13 13:00:00"}
        start_time = temporal_parser._parse_datetime(occurrence_data['start_time'])
        self.assertEqual(start_time, datetime.datetime(2011, 10, 13, 13, 0))
        expected_recurrence_set = set([datetime.datetime(2011, 10, 13, 13, 0), datetime.datetime(2011, 10, 14, 13, 0), datetime.datetime(2011, 10, 15, 13, 0),
                             datetime.datetime(2011, 10, 16, 13, 0), datetime.datetime(2011, 10, 17, 13, 0), datetime.datetime(2011, 10, 18, 13, 0),
                             datetime.datetime(2011, 10, 19, 13, 0), datetime.datetime(2011, 10, 20, 13, 0), datetime.datetime(2011, 10, 21, 13, 0),
                             datetime.datetime(2011, 10, 22, 13, 0), datetime.datetime(2011, 10, 23, 13, 0), datetime.datetime(2011, 10, 24, 13, 0),
                             datetime.datetime(2011, 10, 25, 13, 0), datetime.datetime(2011, 10, 26, 13, 0), datetime.datetime(2011, 10, 27, 13, 0),
                             datetime.datetime(2011, 10, 28, 13, 0), datetime.datetime(2011, 10, 29, 13, 0), datetime.datetime(2011, 10, 30, 13, 0),
                             datetime.datetime(2011, 10, 31, 13, 0), datetime.datetime(2011, 11, 1, 13, 0), datetime.datetime(2011, 11, 2, 13, 0),
                             datetime.datetime(2011, 11, 3, 13, 0), datetime.datetime(2011, 11, 4, 13, 0), datetime.datetime(2011, 11, 5, 13, 0),
                             datetime.datetime(2011, 11, 6, 13, 0), datetime.datetime(2011, 11, 7, 13, 0), datetime.datetime(2011, 11, 8, 13, 0),
                             datetime.datetime(2011, 11, 9, 13, 0), datetime.datetime(2011, 11, 10, 13, 0), datetime.datetime(2011, 11, 11, 13, 0),
                             datetime.datetime(2011, 11, 12, 13, 0), datetime.datetime(2011, 11, 13, 13, 0)])
        recurrence_set = temporal_parser._recurrence_set(occurrence_data)
        self.assertEqual(recurrence_set, expected_recurrence_set)

    def test_multiple_occurrences_with_start_datetime_and_rdates_and_rrules(self):
        occurrence_data = {"recurrence": {"rrules": {"rrule": "FREQ=DAILY;BYHOUR=08;BYMINUTE=00;UNTIL=20110901T235959"},
                    "exrules": None,"rdates": {"rdate": [
                            "2011-10-10 08:00:00", "2011-10-11 08:00:00", "2011-10-12 08:00:00", "2011-10-13 08:00:00",
                            "2011-11-21 08:00:00", "2011-11-22 08:00:00", "2011-11-23 08:00:00", "2011-11-24 08:00:00"]},
                    "description": "on various days","exdates": None}, "start_time": "2011-10-11 08:00:00"}
        expected_recurrence_set = set([datetime.datetime(2011, 10, 10, 8, 0), datetime.datetime(2011, 10, 11, 8, 0), datetime.datetime(2011, 10, 12, 8, 0),
                         datetime.datetime(2011, 10, 13, 8, 0), datetime.datetime(2011, 11, 21, 8, 0), datetime.datetime(2011, 11, 22, 8, 0),
                         datetime.datetime(2011, 11, 23, 8, 0), datetime.datetime(2011, 11, 24, 8, 0)])
        start_time = temporal_parser._parse_datetime(occurrence_data['start_time'])
        self.assertEqual(start_time, datetime.datetime(2011, 10, 11, 8, 0))
        recurrence_set = temporal_parser._recurrence_set(occurrence_data)
        self.assertEqual(recurrence_set, expected_recurrence_set)

    def test_multiple_occurrences_with_start_and_end_datetime_and_rdates_and_rrules(self):
        occurrence_data = {
        "recurrence": { "rrules": { "rrule": "FREQ=WEEKLY;INTERVAL=1;BYDAY=TU;UNTIL=20120315"},
            "exrules": None, "rdates": None, "description": "weekly on Tuesdays until March 15, 2012",
            "exdates": None}, "start_time": "2011-10-11 20:00:00", "stop_time": "2011-10-12 04:00:00"}
        expected_recurrence_set = set([datetime.datetime(2011, 10, 11, 20, 0),
             datetime.datetime(2011, 10, 18, 20, 0), datetime.datetime(2011, 10, 25, 20, 0), datetime.datetime(2011, 11, 1, 20, 0),
             datetime.datetime(2011, 11, 8, 20, 0)])
        start_time = temporal_parser._parse_datetime(occurrence_data['start_time'])
        self.assertEqual(start_time, datetime.datetime(2011, 10, 11, 20, 0))
        stop_time = temporal_parser._parse_datetime(occurrence_data['stop_time'])
        self.assertEqual(stop_time, datetime.datetime(2011, 10, 12, 4, 0))
        recurrence_set = temporal_parser._recurrence_set(occurrence_data)
        self.assertEqual(recurrence_set, expected_recurrence_set)
