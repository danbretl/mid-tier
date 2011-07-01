from importer.parsers.tests import *

from django.test import TestCase
"""
Author: Vikas Menon
Date: April 6th, 2011
-------------------------------------------------
Test case design:
-------------------------------------------------
a) Test the consumer:
    1) Test the ScrapeFeedReader
    2) Test the ScrapeFeedConsumer
        A) Test _wire_all
        B) Test _wire_source
        C) Test _register
        D) Test all properties
        E) Test internal methods (_items)


b) Test the parsers
    1) Test the BaseParser
    2) Test Locations parsers:
        A) Test the CityParser
        B) Test the PointParser
        C) Test the PlaceParser

-------------------------------------------------
Building a simple test_scrape.feed

1) 5 Events
   - Most events have a unique guid, but some events share the same guid.
       - !What should the behavior be in this case?
   - Each event corresponds to 1+ or no categories
       - Test for one category for an event.
       - Test for multiple categories for an event.
       - Test for repeated categories for the same event.
       - Test for missing categories for events.
2) 20 Occurrences
   - Each occurrence corresponds to one or no events.
   - Some occurrences share the same guid.
   - Some occurrences share the same event_guid.
   - Each occurrence corresponds to 1 or no location.
3) 6 Locations
   - !Most locations have a unique guid, but some share the same.
4) 8 categories
   - !Most categories have a unique guid, but some share the same.
-------------------------------------------------
"""
from django.core.management import call_command

class MultiImportTest(TestCase):
    """
    """
    # example usage: call_command('my_command', 'foo', bar='baz')
    fixtures = ['categories', 'sources', 'auth', 'external_categories_all']

    def test_multiImport(self):
        # Create 2 scrape.tar.gz files containing almost similar information
        call_command('unpack_scrapes', 'importer/fixtures/scrape1.tar.gz')
        # Test if command was successful
        import ipdb; ipdb.set_trace()
        call_command('unpack_scrapes', 'importer/fixtures/scrape2.tar.gz')
        # Test is second scrape ran as expected on top of the existing scrape
