import os
from django.test import TestCase
from django.contrib.gis import geos
from importer.ical.adaptors import OccurrenceAdaptor 
from vobject import readOne 
from events.models import Event, Category
from places.models import Place
from django_dynamic_fixture import get, DynamicFixture as F


class TestResourceConsumer(object):
    _RESOURCE_DIR = os.path.join(os.path.dirname(__file__), 'test_resources')

    @classmethod
    def consume_ical(cls):
        filename = os.path.join(cls._RESOURCE_DIR, 'test_ical.ics')
        f = open(filename, 'r')
        event_vobject = readOne(f)
        f.close()
        return event_vobject


class ICalOccurrenceAdaptorTest(TestCase):
    fixtures = ['auth', 'categories', 'sources']

    def setUp(self):
        self.event_vobject = TestResourceConsumer.consume_ical()
        self.adaptor = OccurrenceAdaptor()

    def test_adapt_new_valid(self):
        default_place = get(Place, point=F(geometry=geos.Point(x=0,y=0)))
        default_event = get(Event, concrete_category=Category.objects.get(slug='music'))
        created_occurrences = list(self.adaptor.adapt_m2o(self.event_vobject,
            event=default_event.id, place=default_place.id))

        self.assertEquals(1, len(created_occurrences), 'Unexpected # of occs')

