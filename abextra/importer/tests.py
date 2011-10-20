from importer.parsers.tests import *

from django.test import TestCase
from importer.consumer import ScrapeFeedConsumer
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
    1) Test the BaseAdapter
    2) Test Locations parsers:
        A) Test the CityAdapter
        B) Test the PointAdapter
        C) Test the PlaceAdapter

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
