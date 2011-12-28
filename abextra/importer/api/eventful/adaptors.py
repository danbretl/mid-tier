import HTMLParser
from core.parsers import PriceParser
from importer.adaptors import BaseAdaptor
from importer.forms import ExternalCategoryImportForm
from events.forms import OccurrenceImportForm, EventImportForm
from places.forms import PlaceImportForm, PointImportForm, CityImportForm
from prices.forms import PriceImportForm
import importer.api.eventful.utils as utils

# ========
# = Base =
# ========
class EventfulBaseAdaptor(BaseAdaptor):
    source_name = 'eventful'


# ==========
# = Places =
# ==========
class CityAdaptor(EventfulBaseAdaptor):
    model_form = CityImportForm
    fields = ['city', 'state']
    form_data_map = {'city': 'city', 'state': 'region'}


class PointAdaptor(EventfulBaseAdaptor):
    model_form = PointImportForm
    fields = ['geometry', 'address']
    slave_adaptors = {'city': CityAdaptor}
    form_data_map = {
        'address': 'address',
        'latitude': 'latitude',
        'longitude': 'longitude',
        'zip': 'postal_code',
        'country': 'country_abbr2'
    }


class PlaceAdaptor(EventfulBaseAdaptor):
    model_form = PlaceImportForm
    fields = ['title', 'point']
    slave_adaptors = {'point': PointAdaptor}
    form_data_map = {
        'description': '__kwiqet/venue_details/description',
        'title': '__kwiqet/venue_details/name',
        'url': '__kwiqet/venue_details/url',
    }
    file_data_map = {'image': '__kwiqet/venue_images'}


# ==========
# = Prices =
#===========
class PriceAdaptor(EventfulBaseAdaptor):
    model_form = PriceImportForm
    fields = ['occurrence', 'quantity']
    price_parser = None

    def get_price_parser(self):
        if not PriceAdaptor.price_parser:
            PriceAdaptor.price_parser = PriceParser()
        return PriceAdaptor.price_parser

    def adapt_form_data(self, data, form_data):
        form_data['units'] = 'dollars'
        return form_data

    def adapt_form_data_many(self, raw_data):
        raw_free, raw_price = raw_data.get('free'), raw_data.get('price')
        prices = set()
        if raw_free and int(raw_free):
            prices.add(0)
        elif raw_price:
            prices.update(self.get_price_parser().parse(raw_price))
            prices.discard(0)
        else:
            self.logger.warn('Neither "Free" nor "Price" fields could be found.')
        if not prices:
            self.logger.warn('Unable to adapt prices from %s' % raw_price)
        for price in sorted(prices):
            form_data = {'quantity': price}
            yield form_data

# ==========
# = Events =
# ==========
class OccurrenceAdaptor(EventfulBaseAdaptor):
    model_form = OccurrenceImportForm
    fields = ['event', 'start_date', 'place', 'start_time']
    slave_adaptors = {'place': PlaceAdaptor}
    slave_adaptors_to_many = [PriceAdaptor]

    def adapt_form_data_many(self, raw_data):
        start_datetimes, duration, is_all_day = utils.temporal_parser.occurrences(raw_data)
        for start_datetime in start_datetimes:
            form_data = {
                'start_date': start_datetime.date(),
                'start_time': start_datetime.time(),
                'is_all_day': is_all_day
            }
            if duration:
                end_datetime = start_datetime + duration
                form_data.update(end_date=end_datetime.date(), end_time=end_datetime.time())
            yield form_data


class CategoryAdaptor(EventfulBaseAdaptor):
    model_form = ExternalCategoryImportForm
    fields = ['source', 'xid']
    form_data_map = {'xid': 'id'}

    def __init__(self):
        super(CategoryAdaptor, self).__init__()
        self.html_parser = HTMLParser.HTMLParser()

    def adapt_form_data(self, data, form_data):
        name = data.get('name')
        if name:
            form_data['name'] = self.html_parser.unescape(name)
        return form_data


class EventAdaptor(EventfulBaseAdaptor):
    model_form = EventImportForm
    fields = ['xid', ]
    slave_adaptors_to_many = [OccurrenceAdaptor]
    form_data_map = {
        'xid': 'id',
        'title': 'title',
        'description': 'description',
        'url': 'url',
        'image_url': 'image/url'
    }
    file_data_map = {'image': '__kwiqet/event_images'}

    def __init__(self):
        super(EventAdaptor, self).__init__()
        self.external_category_adaptor = CategoryAdaptor()

    def adapt_form_data(self, data, form_data):
        external_category_ids = []
        categories = data.get('categories')
        if categories:
            category_wrapper = categories.get('category')
            if category_wrapper:
                categories_raw = [category_wrapper] if not isinstance(category_wrapper, list) else category_wrapper
                for raw_category in categories_raw:
                    created, external_category = self.external_category_adaptor.adapt(raw_category)
                    if external_category:
                        external_category_ids.append(external_category.id)

        form_data['external_categories'] = external_category_ids
        return form_data
