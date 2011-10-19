import core.parsers
import HTMLParser

from importer.parsers.base import BaseParser
from importer.forms import ExternalCategoryImportForm
from events.forms import OccurrenceImportForm, EventImportForm
from places.forms import PlaceImportForm, PointImportForm, CityImportForm
from prices.forms import PriceImportForm

import importer.parsers.utils as utils 

SOURCE_NAME = 'eventful'

class EventfulPriceParser(BaseParser):
    model_form = PriceImportForm
    fields = ['occurrence', 'quantity']

    def parse_form_data(self, data, form_data):
        form_data['occurrence'] = data.get('occurrence')
        form_data['units'] = 'dollar'
        form_data['quantity'] = data.get('quantity')
        return form_data

class EventfulCityParser(BaseParser):
    model_form = CityImportForm
    fields = ['city', 'state']

    def parse_form_data(self, data, form_data):
        form_data['city'] = data.get('city')
        form_data['state'] = data.get('region')
        return form_data

class EventfulPointParser(BaseParser):
    model_form = PointImportForm
    fields = ['latitude', 'longitude', 'address']
    slave_adapters = {'city': EventfulCityParser}

    def parse_form_data(self, data, form_data):
        # Also possible, get an address from lat long?
        # Keeping the address compulsory for now for sanity.
        form_data['address'] = data.get('address')
        form_data['latitude'] = data.get('latitude')
        form_data['longitude'] = data.get('longitude')
        zipcode = data.get('postal_code')
#        if not zipcode:
#            from pygeocoder import Geocoder
#            results = Geocoder.reverse_geocode(
#                *map(float, map(form_data.get, ('latitude', 'longitude')))
#            )
#            zipcode = results[0].postal_code
#            print "\n\n\n zipcode: %s\n\n\n" % zipcode
        form_data['zip'] = zipcode
        form_data['country'] = data.get('country_abbr2')
        return form_data

class EventfulPlaceParser(BaseParser):
    model_form = PlaceImportForm
    slave_adapters = {'point': EventfulPointParser}
    fields = ['title', 'point']
    form_data_map = {
        'phone': 'phone',
        'title': 'venue_details/name',
        'url': 'venue_details/url',
    }
    file_data_map = {'image': 'venue_images_local'}

class EventfulCategoryParser(BaseParser):
    model_form = ExternalCategoryImportForm
    fields = ['source', 'xid']

    def __init__(self):
        super(EventfulCategoryParser, self).__init__()
        self.html_parser = HTMLParser.HTMLParser()

    def parse_form_data(self, data, form_data):
        form_data['source'] = SOURCE_NAME
        form_data['xid'] = data.get('id')
        name = data.get('name')
        if name:
            form_data['name'] = self.html_parser.unescape(name)
        return form_data

class EventfulOccurrenceParser(BaseParser):
    model_form = OccurrenceImportForm
    fields = ['event', 'start_date', 'place', 'start_time']
    slave_adapters = {'place': EventfulPlaceParser}
    slave_adapters_o2m = {'o2m_prices': EventfulPriceParser}
    form_data_map = {
        'event': 'event',
        'start_time': 'start_time',
        'start_date': 'start_date'
    }
    o2m_default_field = 'occurrence'

    def __init__(self):
        super(EventfulOccurrenceParser, self).__init__()
        self.quantity_parser = core.parsers.PriceParser()

    def o2m_prices(self, data):
        return utils.expand_prices(data, self.quantity_parser)
        
class EventfulEventParser(BaseParser):
    model_form = EventImportForm
    fields = ['xid',]
    img_dict_key = 'image_local'
    slave_adapters_o2m = {'o2m_occurrences': EventfulOccurrenceParser}
    o2m_default_field = 'event'

    def __init__(self):
        super(EventfulEventParser, self).__init__()
        self.external_category_parser = EventfulCategoryParser()

    def parse_form_data(self, data, form_data):
        form_data['source'] = SOURCE_NAME
        form_data['xid'] = data.get('id')
        form_data['title'] = data.get('title')
        form_data['description'] = data.get('description')
        form_data['url'] = data.get('url')
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

        # process image attachments
        image = data.get('image')
        if image:
            form_data['image_url'] = image['url']

        return form_data

    def o2m_occurrences(self, data):
        return utils.expand_occurrences(data)

    def post_parse(self, data, instance):
        event = instance
        # sanity check  FIXME ugly
        occurrence_count = event.occurrences.count()
        if not occurrence_count:
            self.logger.warn('Dropping Event: no parsable occurrences')
            event.delete()
