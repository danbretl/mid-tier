"""
Author: Vikas Menon
Date: April 6th, 2011

"""
from importer.parsers.tests import *
from django.test import TestCase
from importer.consumer import ScrapeFeedConsumer
from ical import Parser, DictObj
from datetime import datetime
from importer.parsers.event import EventParser
from events.models import Source, Occurrence
from prices.models import Price

class iCalParserTest(TestCase):
    fixtures = ['categories', 'auth', 'sources']
    raw_location = {
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

    source = Source.objects.get(name='iCal')
    raw_occurrence = DictObj({
        'start_date' : datetime.now().date(),
        'start_time' : datetime.now().time(),
        'location'   : raw_location,
        'prices'     : Price.objects.none()
        })
    raw_event = DictObj({
        'title' : 'Fun Event 1',
        'url'   : 'www.google.com',
        'description': 'ABC',
        'submitted_by' : 'iCal parser',
        'source' : source,
        'occurrences' : [raw_occurrence]
        })


    def test_insert_location_info(self):
        parser = PlaceParser()
        try:
            parser.parse(self.raw_location)
        except:
            self.fail('Place Parser failed at parsing raw_dict')

    def test_insert_event_dict(self):
        parser = EventParser()
        try:
            parser.parse(self.raw_event)
        except:
            self.fail('Event parser failed at parsing raw_dict')

    def test_Parser(self):
        parser = Parser()
        file_path = 'importer/fixtures/test_ical.ics'
        file_url = 'https://www.google.com/calendar/ical/mtj7g3j1jeivh80p2qa77fse0o%40group.calendar.google.com/public/basic.ics'
        ical_parser = Parser(None,'::', file_url)
        try:
            ical_parser.get_events()
        except:
            self.fail('Could not run ical parser for urls')
        ical_parser = Parser(file_path)
        try:
            ical_parser.get_events()
        except:
            self.fail('Could not run ical parser from file')
