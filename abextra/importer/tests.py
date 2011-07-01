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
from events.models import Event, Occurrence

class MultiImportTest(TestCase):
    """
    """
    # example usage: call_command('my_command', 'foo', bar='baz')
    fixtures = ['categories', 'sources', 'auth', 'external_categories_all']

    def assert_event_counts(self):
        calculated_count = len(Event.objects.all())
        # (This could be a script that returns the number of events in the scrape feed
        # hardcoding to 1 for now.
        expected_count = 1
        self.assertEqual(calculated_count, expected_count)

    def assert_occurrence_counts(self, event, num):
        # This test should be made more robust (like for only a particular event
        calculated_count = len(Occurrence.objects.filter(event=event))
        self.assertEqual(calculated_count, num)


    def test_multiImport(self):
        # Create 2 scrape.tar.gz files containing almost similar information
        call_command('unpack_scrapes', 'importer/fixtures/scrape1.tar.gz')
        self.assert_event_counts()
        # Test if command was successful
        event = Event.objects.get(title__contains='X-Men')
        self.assert_occurrence_counts(event, 1)
        call_command('unpack_scrapes', 'importer/fixtures/scrape2.tar.gz')
        # Test is second scrape ran as expected on top of the existing scrape
        self.assert_event_counts()
        self.assert_occurrence_counts(event, 2)

