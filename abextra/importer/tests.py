from importer.parsers.tests import *

from django.test import TestCase
"""
Author: Vikas Menon
Date: April 6th, 2011
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
        # Test if command was successful
        import ipdb; ipdb.set_trace()
        call_command('unpack_scrapes', 'importer/fixtures/scrape2.tar.gz')
        # Test is second scrape ran as expected on top of the existing scrape
        self.assert_event_counts()
        self.assert_occurrence_counts(event, 2)
