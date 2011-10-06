import re
import os
import datetime
import HTMLParser
import dateutil.parser
import dateutil.rrule
from django.conf import settings
from itertools import chain
from importer.parsers.base import BaseParser
from importer.parsers.locations import PlaceParser, PointParser, CityParser
from importer.parsers.price import PriceParser
from importer.forms import ExternalCategoryImportForm
from events.forms import OccurrenceImportForm, EventImportForm
from events.models import Source, EventSummary
from events.utils import CachedCategoryTree
from importer.parsers.event import ExternalCategoryParser
from importer.parsers.event import EventParser, OccurrenceParser

_quantity_re = re.compile(r'(\d+(?:\.\d{2})?)|free')

# FIXME: this kind of regex logic should not be in a parser;
# refactor to a form later so it's not muddying up the parsers

class SoldOutException(Exception):
    """Usually raised by price parser generators."""
    pass

def parse_prices(price_string):
        price_string = price_string.lower()
        prices = _quantity_re.findall(price_string)
        if not prices:
            if 'sold out' in price_string:
                raise SoldOutException()
            else:
                return None
        return tuple(price if price else '0.00' for price in prices)



class EventfulPriceParser(PriceParser):

    def parse_form_data(self, data, form_data):
        form_data['occurrence'] = data.get('occurrence')
        form_data['units'] = 'dollar'
        if data.get('free'):
            if int(data.get('free')):
                form_data['quantity'] = '0.00'
        else:
            quantities = parse_prices(data.get('price'))
            try:
                form_data['quantity'] = quantities[0]
            except:
                self.logger.warn('Error parsing price <%s>' % data.get('price'))
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

    def reformat_time(time):
        # reformat time into in HH:MM[:ss[.uuuuuu]] format.
        pass


    def parse_form_data(self, data, form_data):
        form_data['event'] = data.get('event')
        form_data['start_date'] = data.get('start_date')
        form_data['end_date'] = data.get('end_date')
        try:
            t_i = dateutil.parser.parse(data.get('start_time'))
            if data.get('stop_time'):
                t_f = dateutil.parser.parse(data.get('stop_time'))
            else:
                t_f = t_i
        except:
            self.logger.warn("Error parsing occurrence for eventful event <%s>" % data.get('title'))
        else:
            form_data['start_date'] = t_i.strftime("%Y-%m-%d")
            form_data['end_date'] = t_f.strftime("%Y-%m-%d")
            form_data['start_time'] = t_i.strftime("%H:%M:%S")
            form_data['end_time'] = t_f.strftime("%H:%M:%S")


            created, place = self.place_parser.parse(data)
            form_data['place'] = place.id if place else None

        return form_data

    def post_parse(self, data, instance):
        occurrence = instance

        # prices
        price = data.get('price')
        if price:
            data['occurrence'] = occurrence.id
            self.price_parser.parse(data)

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

    def post_parse(self, data, instance):
        event = instance
        # occurrences
        recurrence_dict = data.get('recurrence')
        if recurrence_dict:
            rdates, rrules = map(recurrence_dict.get, ('rdates', 'rrules'))
            if rdates:
                rdate = rdates.get('rdate')
                if rdate:
                    if not isinstance (rdate, (tuple, list)):
                        rdate = [rdate]
                    for date in rdate:
                        occurrence_form_data = data.copy()
                        occurrence_form_data['event'] = event.id
                        occurrence_form_data['start_time'] = date
                        self.occurrence_parser.parse(occurrence_form_data)

            if rrules:
                rrule_field = rrules.get('rrule')
                if rrule_field:
                    rrules = rrule_field if isinstance(rrule_field, (list, tuple)) else [rrule_field]
                    for rrule in rrules:
                        rrule_cleaned = rrule.replace('BYDAY','BYWEEKDAY')
                        results = dateutil.rrule.rrulestr(rrule_cleaned)
                        dates = chain(*(r[:settings.MAX_RECURRENCE] for r in results))
                        for date in dates:
                            occurrence_form_data = data.copy()
                            occurrence_form_data['event'] = event.id
                            if not isinstance(date, datetime.datetime):
                                self.logger.warn('This is not a datetime.') 
                            occurrence_form_data['start_time'] = date.strftime('%x %X')
                            self.occurrence_parser.parse(occurrence_form_data)
                            # print 'Total occurrences for %s: %d' % (event.id,
                                    # event.occurrences.count())

        # sanity check  FIXME ugly
        occurrence_count = event.occurrences.count()
        if not occurrence_count:
            self.logger.warn('Dropping Event: no parsable occurrences')
            event.delete()
            return


