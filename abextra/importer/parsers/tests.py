from django.test import TestCase
from django.conf import settings
from importer.consumer import ScrapeFeedConsumer
from importer.eventful_api.loader import EventfulApiConsumer
from importer.parsers.locations import CityParser, PointParser, PlaceParser
from importer.parsers.event import OccurrenceParser, EventParser, ExternalCategoryParser
from importer.parsers.price import PriceParser
from importer.parsers.eventful import EventfulEventParser
from importer.eventful_import import EventfulImporter

# class ExternalCategoryParserTest(TestCase):
#     fixtures = ['sources'] # ,'external_categories']
#     # consumer = ScrapeFeedConsumer()
#     parser = ExternalCategoryParser()
#
#     def test_parse(self):
#         for category in self.consumer.categories:
#             self.parser.parse(category)
#
# class CityParserTest(TestCase):
#     # consumer = ScrapeFeedConsumer()
#     parser = CityParser()
#
#     def test_parse(self):
#         for location in self.consumer.locations:
#             self.parser.parse(location)
#
# class PointParserTest(TestCase):
#     # consumer = ScrapeFeedConsumer()
#     parser = PointParser()
#
#     def test_parse(self):
#         for location in self.consumer.locations:
#             self.parser.parse(location)
#
# class PlaceParserTest(TestCase):
#     # consumer = ScrapeFeedConsumer()
#     parser = PlaceParser()
#
#     def test_parse(self):
#         for location in self.consumer.locations:
#             self.parser.parse(location)
#
# class PriceParserTest(TestCase):
#     fixtures = ['events']
#     # consumer = ScrapeFeedConsumer()
#     parser = PriceParser()
#
#     def test_parse(self):
#         for price in self.consumer.prices:
#             price['occurrence'] = 1
#             self.parser.parse(price)
#
# class OccurrenceParserTest(TestCase):
#     fixtures = ['events']
#     # consumer = ScrapeFeedConsumer()
#     parser = OccurrenceParser()
#
#     def test_parse(self):
#         for occurrence in self.consumer.occurrences:
#             self.parser.parse(occurrence)

class EventParserTest(TestCase):
    fixtures = ['auth', 'categories', 'sources', 'external_categories']

    def setUp(self):
        self.consumer = ScrapeFeedConsumer()
        self.parser = EventParser()

    def test_parse(self):
        for event in self.consumer.events():
            self.parser.parse(event)

class EventfulParserTest(TestCase):
    fixtures = ['auth', 'categories', 'sources', 'external_categories']

    def setUp(self):
        # self.consumer = SimpleApiConsumer()
        # self.parser = EventfulEventParser()
        self.importer = EventfulImporter(page_size=100, total_pages=2)

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
        # self.parser = EventfulEventParser()
        self.importer = EventfulImporter(page_size=10, current_page=1,
                total_pages=3, mock_api=False, make_dumps=True)

    def test_parse(self):
        (created_events, existing_events) = self.importer.import_events()
        assert(created_events)
        for e in created_events:
            if e.id:
                e.delete()
        self.importer = EventfulImporter(page_size=10, current_page=1,
                total_pages=3, mock_api=True, make_dumps=False)
        (created_mock_events, existing_events) = self.importer.import_events()
        assert(created_mock_events)

        # for event in events:
            # try:
                # event_obj = self.parser.parse(event)
            # except ValueError as parse_err:
                # self.logger.warn("Encountered exception while parsing:")
                # self.logger.warn(parse_err.args)

class EventfulParserDateParsingTest(TestCase):
    fixtures = ['auth', 'categories', 'sources', 'external_categories']

    def setup(self):
        self.consumer = EventfulApiConsumer(mock_api=True,
                dump_sub_dir='p10-c100')

    def test_single_rdate_and_rrules(self):
        event_id = 'E0-001-037594896-6@2011101110'
        event_data = self.consumer.fetch_event_details(event_id)
        # stub for now
        assert event_data

