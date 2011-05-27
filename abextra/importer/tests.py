from importer.parsers.tests import *

from django.test import TestCase
from importer.consumer import ScrapeFeedConsumer
"""
Author: Vikas Menon
Date: April 6th, 2011

"""
from ical import Parser
from importer.parsers.locations import PlaceParser

class iCalParserTest(TestCase):
    def test_init(self):
        # Expects atleast 1 argument
        self.assertRaises(TypeError, Parser)

    def test_insert_location_info(self):
        parser = PlaceParser()
        raw_dict = {
            'city'   : 'New York',
            'state'  : 'NY',
            'title'  : 'TestLocation',
            'phone'  : '732-999-9999',
            'url'    : 'http://www.google.com',
            'address': '93 Leonard Street',
            'zipcode': '10013',
            'country': 'US',
            'image' : 'http://www.google.com/images/logos/ps_logo2.png',
            }
        parser.parse(raw_dict)
