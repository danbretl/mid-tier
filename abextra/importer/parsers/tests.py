from django.test import TestCase
from django.conf import settings
from events.models import Event
from importer.consumer import ScrapeFeedConsumer
from importer.eventful.consumer import EventfulApiConsumer
from importer.parsers.locations import CityAdapter, PointAdapter, PlaceAdapter
from importer.parsers.event import OccurrenceAdapter, EventAdapter, ExternalCategoryAdapter
from importer.parsers.price import PriceAdapter
from importer.parsers.adapters import EventAdapter
from importer.parsers.utils import *
from importer.eventful_import import EventfulPaginator

# class ExternalCategoryParserTest(TestCase):
#     fixtures = ['sources'] # ,'external_categories']
#     # consumer = ScrapeFeedConsumer()
#     parser = ExternalCategoryAdapter()
#
#     def test_parse(self):
#         for category in self.consumer.categories:
#             self.parser.parse(category)
#
# class CityParserTest(TestCase):
#     # consumer = ScrapeFeedConsumer()
#     parser = CityAdapter()
#
#     def test_parse(self):
#         for location in self.consumer.locations:
#             self.parser.parse(location)
#
# class PointParserTest(TestCase):
#     # consumer = ScrapeFeedConsumer()
#     parser = PointAdapter()
#
#     def test_parse(self):
#         for location in self.consumer.locations:
#             self.parser.parse(location)
#
# class PlaceParserTest(TestCase):
#     # consumer = ScrapeFeedConsumer()
#     parser = PlaceAdapter()
#
#     def test_parse(self):
#         for location in self.consumer.locations:
#             self.parser.parse(location)
#
# class PriceParserTest(TestCase):
#     fixtures = ['events']
#     # consumer = ScrapeFeedConsumer()
#     parser = PriceAdapter()
#
#     def test_parse(self):
#         for price in self.consumer.prices:
#             price['occurrence'] = 1
#             self.parser.parse(price)
#
# class OccurrenceParserTest(TestCase):
#     fixtures = ['events']
#     # consumer = ScrapeFeedConsumer()
#     parser = OccurrenceAdapter()
#
#     def test_parse(self):
#         for occurrence in self.consumer.occurrences:
#             self.parser.parse(occurrence)

# class EventParserTest(TestCase):
    # fixtures = ['auth', 'categories', 'sources', 'external_categories']

    # def setUp(self):
        # self.consumer = ScrapeFeedConsumer()
        # self.parser = EventAdapter()

    # def test_parse(self):
        # for event in self.consumer.events():
            # self.parser.parse(event)

class EventfulParserTest(TestCase):
    fixtures = ['auth', 'categories', 'sources', 'external_categories']

    def setUp(self):
        # self.consumer = SimpleApiConsumer()
        # self.parser = EventAdapter()
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
        # self.parser = EventAdapter()
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

class EventfulParserDateParsingTest(TestCase):
    fixtures = ['auth', 'categories', 'sources', 'external_categories']

    def test_single_rdate_and_rrules(self):
        consumer = EventfulApiConsumer(mock_api=True, dump_sub_dir='p10-c100')

        # 43e64022c8ff8aff4ad920e565bd62c5.json

        event_id = 'E0-001-037594896-6@2011101110'
        event_data = consumer.fetch_event_details(event_id)
        recurrences = event_data.get('recurrence')

        # ipdb> event_data['start_time']
        # '2011-10-11 10:00:00'
        # ipdb> event_data['stop_time']
        # '2011-10-11 16:30:00'
        # event_data['recurrence'] looks like this
        # {'rrules': {'rrule': 'FREQ=DAILY;UNTIL=20111028'}, 'exrules': None, 'rdates': {'rdate': '2011-04-30 10:00:00'}, 'description': 'on various days', 'exdates': None}

        (start_datetime, duration) = parse_start_datetime_and_duration(event_data)
        (first_datetime, current_date_times) = expand_recurrence_dict(recurrences,
                start_datetime)

        # ipdb> first_occ
        # datetime.datetime(2011, 4, 30, 10, 0)
        # ipdb> start_datetime
        # datetime.datetime(2011, 10, 11, 10, 0)

        self.assertTrue(first_datetime < start_datetime)

        # so we can have a first occurrence before the starting datetime

        self.assertEqual(duration, datetime.timedelta(hours=6,minutes=30))

        # and our durations are getting calculated correctly

        self.assertFalse(current_date_times)

        # and the date times have all been clipped (because they're all in the
        # past as of 2011-10-14

        # now, let's test that it's getting all the recurrences originally
        # before being clipped

        (first_occ, current_date_times) = expand_recurrence_dict(recurrences,
                start_datetime, clip_before=first_datetime)

        self.assertTrue(current_date_times)

