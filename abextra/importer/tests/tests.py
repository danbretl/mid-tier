"""
Author: Vikas Menon
Date: April 6th, 2011
#################################################
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

Criteria: 
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
     - In the case where they share the same guid:
       - In some cases, locations are identical
       - In the rest, locationss are distinct
4) 8 categories
   - !Most categories have a unique guid, but some share the same. 
-------------------------------------------------
#################################################
"""

from django.test import TestCase


class SimpleTest(TestCase):


    def test_load_fee(self):
        """
        
        Arguments:
        - `self`:
        """
        consumer = ScrapeFeedConsumer('./test.feed')
        """
        parser = PlaceParser()
        for location in consumer.locations:
            yield parser.parse(location)
        """
    
