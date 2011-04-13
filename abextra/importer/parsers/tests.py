from django.test import TestCase
from importer.consumer import ScrapeFeedConsumer
from importer.parsers.locations import CityParser, PointParser, PlaceParser
from importer.parsers.event import OccurrenceParser, EventParser, ExternalCategoryParser

class ExternalCategoryParserTest(TestCase):
    fixtures = ['sources'] # ,'external_categories']
    consumer = ScrapeFeedConsumer()
    parser = ExternalCategoryParser()

    def test_parse(self):
        for category in self.consumer.categories:
            print self.parser.parse(category)

class CityParserTest(TestCase):
    consumer = ScrapeFeedConsumer()
    parser = CityParser()

    def test_parse(self):
        for location in self.consumer.locations:
            print self.parser.parse(location)

class PointParserTest(TestCase):
    consumer = ScrapeFeedConsumer()
    parser = PointParser()

    def test_parse(self):
        for location in self.consumer.locations:
            print self.parser.parse(location)

class PlaceParserTest(TestCase):
    consumer = ScrapeFeedConsumer()
    parser = PlaceParser()

    def test_parse(self):
        for location in self.consumer.locations:
            print self.parser.parse(location)


class OccurrenceParserTest(TestCase):
    fixtures = ['events']
    consumer = ScrapeFeedConsumer()
    parser = OccurrenceParser()

    def test_parse(self):
        for occurrence in self.consumer.occurrences:
            print self.parser.parse(occurrence)

class EventParserTest(TestCase):
    fixtures = ['categories', 'sources', 'external_categories']
    consumer = ScrapeFeedConsumer()
    parser = EventParser()

    def test_parse(self):
        for event in self.consumer.events:
            self.parser.parse(event)
        # import ipdb; ipdb.set_trace()