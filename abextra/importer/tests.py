from django.test import TestCase
from importer.consumer import ScrapeFeedConsumer
from importer.parsers.locations import PlaceParser


class ScrapeTest(TestCase):
    """
    """
    def test_import(self):
        consumer = ScrapeFeedConsumer('test.feed')
        
