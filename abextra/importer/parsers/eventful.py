import re
import os
import datetime
import HTMLParser
import dateutil.parser
import dateutil.rrule
from django.conf import settings
from itertools import chain
import core.parsers
from importer.forms import ExternalCategoryImportForm
from events.forms import OccurrenceImportForm, EventImportForm
from events.models import Source, EventSummary
from events.utils import CachedCategoryTree
from importer.parsers.base import BaseParser

# FIXME these should not be inhereted from directly
from importer.parsers.event import ExternalCategoryParser
from importer.parsers.event import EventParser, OccurrenceParser
from importer.parsers.locations import PlaceParser, PointParser, CityParser
from importer.parsers.price import PriceParser
from importer.parsers.utils import *

class EventfulPriceParser(PriceParser):

    def parse_form_data(self, data, form_data):
        form_data['occurrence'] = data.get('occurrence')
        form_data['units'] = 'dollar'
        form_data['quantity'] = data.get('quantity') 
        return form_data

class EventfulCityParser(CityParser):

    def parse_form_data(self, data, form_data):
        form_data['city'] = data.get('city')
        form_data['state'] = data.get('region')
        #TODO: Try and get this from geocoding information.
        return form_data

class EventfulPointParser(PointParser):
    city_parser = EventfulCityParser()

    def parse_form_data(self, data, form_data):
        # Also possible, get an address from lat long?
        # Keeping the address compulsory for now for sanity.
        form_data['address'] = data.get('address') or ''
        form_data['latitude'] = data.get('latitude')
        form_data['longitude'] = data.get('longitude')
        # FIXME: deal with form_data not having zip code
        form_data['zip'] = data.get('postal_code') or '10000'
        form_data['country'] = 'US'
        created, city = self.city_parser.parse(data)
        if city:
            form_data['city'] = city.id
        return form_data

class EventfulPlaceParser(PlaceParser):
    point_parser = EventfulPointParser()
    img_dict_key='venue_image_local'

    def parse_form_data(self, data, form_data):
        created, point = self.point_parser.parse(data)
        if point:
            form_data['point'] = point.id

        venue_details = data.get('venue_details')
        if venue_details:
            form_data['title'] = venue_details.get('name')
            form_data['phone'] = data.get('phone') or ''
            form_data['url'] = venue_details.get('url')

        venue_images = data.get('venue_image_local')
        if venue_images:
            form_data['venue_image_local'] = venue_images
        return form_data

class EventfulCategoryParser(ExternalCategoryParser):
    model_form = ExternalCategoryImportForm
    html_parser = HTMLParser.HTMLParser()
    fields = ['source', 'xid']

    def parse_form_data(self, data, form_data):
        form_data['source'] = 'eventful'
        form_data['xid'] = data.get('id')
        name = data.get('name')
        if name:
            form_data['name'] = self.html_parser.unescape(name)
        return form_data

class EventfulOccurrenceParser(OccurrenceParser):
    model_form = OccurrenceImportForm
    fields = ['event', 'start_date', 'place', 'start_time']
    place_parser = EventfulPlaceParser()
    price_parser = EventfulPriceParser()

    def __init__(self, *args, **kwargs):
        super(EventfulOccurrenceParser, self).__init__(*args, **kwargs)
        self.quantity_parser = core.parsers.PriceParser()

    def parse_form_data(self, data, form_data):
        form_data['event'] = data.get('event')
        form_data['start_time'] = data.get('start_time')
        form_data['start_date'] = data.get('start_date')

        # parse place
        created, place = self.place_parser.parse(data)
        form_data['place'] = place.id if place else None

        return form_data

    def post_parse(self, data, instance):
        occurrence = instance

        # prices
        raw_free = data.get('free')
        raw_price = data.get('price')
        # strange int check cause '1' or '0' comes back as a string
        if raw_free and int(raw_free):
            prices = [0.00]
        elif raw_price:
            prices = self.quantity_parser.parse(raw_price)
        else:
            prices = []
            self.logger.warn('"Free" nor "Price" fields could not be found.')
        for price in prices:
            price_data = {}
            price_data['occurrence'] = occurrence.id
            price_data['quantity'] = str(price)
            self.price_parser.parse(price_data)

class EventfulEventParser(EventParser):
    occurrence_parser = EventfulOccurrenceParser()
    external_category_parser = EventfulCategoryParser()
    img_dict_key='image_local'

    def parse_form_data(self, data, form_data):
        form_data['source'] = 'eventful'
        form_data['xid'] = data.get('id')
        form_data['title'] = data.get('title')
        form_data['description'] = data.get('description')
        form_data['url'] = data.get('url')
        # form_data['popularity_score'] = data.get('popularity_score')
        external_category_ids = []
        categories = data.get('categories')
        if categories:
            category_wrapper =  categories.get('category')
            if category_wrapper:
                if not isinstance(category_wrapper, (list, tuple)):
                    categories = [category_wrapper]
                else:
                    categories = category_wrapper

                for category_data in categories:
                    created, external_category = self.external_category_parser.parse(category_data)
                    if external_category:
                        external_category_ids.append(external_category.id)

        form_data['external_categories'] = external_category_ids
        # FIXME: incorporate eventlet image fetcher before crawler
        # parses but after search results and individual events are
        # crawled

        image = data.get('image')

        if image:
            form_data['image_url'] = image['url']

        return form_data

    def parse_occurrence(self, data, event, start_datetime, duration):
        occurrence_form_data = data
        occurrence_form_data['event'] = event.id
        occurrence_form_data['start_date'] = \
            start_datetime.date().isoformat()
        occurrence_form_data['start_time'] = \
            start_datetime.time().isoformat()
        if duration:
            end_datetime = start_datetime + duration
            occurrence_form_data['end_date'] = \
                end_datetime.date().isoformat()
            occurrence_form_data['end_time'] = \
                end_datetime.time().isoformat()

        self.occurrence_parser.parse(occurrence_form_data)


    def post_parse(self, data, instance):
        self.logger.debug('<%s, %s>' % (data.get('start_date'), data.get('start_time')))
        event = instance
        (start_datetime, duration) = parse_start_datetime_and_duration(data)
        recurrence_dict = data.get('recurrence')
        if recurrence_dict:
            (first_recurrence, current_date_times) = expand_recurrence_dict(recurrence_dict, start_datetime)
            for date_time in current_date_times:
                self.parse_occurrence(data, event, date_time, duration)
        # sanity check  FIXME ugly
        occurrence_count = event.occurrences.count()
        if not occurrence_count:
            self.logger.warn('Dropping Event: no parsable occurrences')
            event.delete()
            return


