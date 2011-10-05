from django.test import TestCase
from importer.consumer import ScrapeFeedConsumer
from importer.eventful_api.loader import SimpleApiConsumer
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
        self.importer = EventfulImporter(page_size=100)

    def test_parse(self):
        events = self.importer.import_events(total_pages=2) 
        # for event in events:
            # try:
                # event_obj = self.parser.parse(event)
            # except ValueError as parse_err:
                # self.logger.warn("Encountered exception while parsing:")
                # self.logger.warn(parse_err.args)


