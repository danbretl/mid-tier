import core.parsers
import HTMLParser
from importer.adaptors import BaseAdapter
from importer.forms import ExternalCategoryImportForm
from events.forms import OccurrenceImportForm, EventImportForm
from places.forms import PlaceImportForm, PointImportForm, CityImportForm
from prices.forms import PriceImportForm
import importer.api.eventful.utils as utils

class EventfulBaseAdapter(BaseAdapter):
    source_name = 'eventful'


class PriceAdapter(EventfulBaseAdapter):
    model_form = PriceImportForm
    fields = ['occurrence', 'quantity']
    form_data_map = {'occurrence': 'occurrence',
                     'quantity': 'quantity'
    }

    def adapt_form_data(self, data, form_data):
        form_data['units'] = 'dollars'
        return form_data


class CityAdapter(EventfulBaseAdapter):
    model_form = CityImportForm
    fields = ['city', 'state']
    form_data_map = {'city': 'city', 'state': 'region'}


class PointAdapter(EventfulBaseAdapter):
    model_form = PointImportForm
    fields = ['latitude', 'longitude', 'address']
    slave_adapters = {'city': CityAdapter}
    form_data_map = {
        'address': 'address',
        'latitude': 'latitude',
        'longitude': 'longitude',
        'zip': 'postal_code',
        'country': 'country_abbr2'
    }


class PlaceAdapter(EventfulBaseAdapter):
    model_form = PlaceImportForm
    slave_adapters = {'point': PointAdapter}
    fields = ['title', 'point']
    form_data_map = {
        'phone': 'phone',
        'title': 'venue_details/name',
        'url': 'venue_details/url',
        }
    file_data_map = {'image': 'venue_images_local'}


class CategoryAdapter(EventfulBaseAdapter):
    model_form = ExternalCategoryImportForm
    fields = ['source', 'xid']
    form_data_map = {'xid': 'id'}

    def __init__(self):
        super(CategoryAdapter, self).__init__()
        self.html_parser = HTMLParser.HTMLParser()

    def adapt_form_data(self, data, form_data):
        name = data.get('name')
        if name:
            form_data['name'] = self.html_parser.unescape(name)
        return form_data


class OccurrenceAdapter(EventfulBaseAdapter):
    model_form = OccurrenceImportForm
    fields = ['event', 'start_date', 'place', 'start_time']
    slave_adapters = {'place': PlaceAdapter}
    slave_adapters_o2m = {'o2m_prices': PriceAdapter}
    form_data_map = {
        'event': 'event',
        'start_time': 'start_time',
        'start_date': 'start_date'
    }
    o2m_default_field = 'occurrence'

    def __init__(self):
        super(OccurrenceAdapter, self).__init__()
        self.quantity_parser = core.parsers.PriceParser()

    def o2m_prices(self, data):
        return utils.expand_prices(data, self.quantity_parser)


class EventAdapter(EventfulBaseAdapter):
    model_form = EventImportForm
    fields = ['xid', ]
    img_dict_key = 'image_local'
    slave_adapters_o2m = {'o2m_occurrences': OccurrenceAdapter}
    form_data_map = {
        'xid': 'id',
        'title': 'title',
        'description': 'description',
        'url': 'url',
        'image_url': 'image/url'
    }
    file_data_map = {'image': 'event_images_local'}
    o2m_default_field = 'event'

    def __init__(self):
        super(EventAdapter, self).__init__()
        self.external_category_adapter = CategoryAdapter()

    def adapt_form_data(self, data, form_data):
        external_category_ids = []
        categories = data.get('categories')
        if categories:
            category_wrapper = categories.get('category')
            if category_wrapper:
                if not isinstance(category_wrapper, (list, tuple)):
                    categories = [category_wrapper]
                else:
                    categories = category_wrapper

                for category_data in categories:
                    created, external_category = self.external_category_adapter.parse(category_data)
                    if external_category:
                        external_category_ids.append(external_category.id)

        form_data['external_categories'] = external_category_ids
        return form_data

    def o2m_occurrences(self, data):
        return utils.expand_occurrences(data)

    def post_adapt(self, data, instance):
        event = instance
        # FIXME ugly sanity check
        occurrence_count = event.occurrences.count()
        if not occurrence_count:
            self.logger.warn('Dropping Event: no parsable occurrences')
            event.delete()
