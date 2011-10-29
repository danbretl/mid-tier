import datetime
import HTMLParser
from importer.adaptors import BaseAdaptor
from importer.forms import ExternalCategoryImportForm
from events.forms import OccurrenceImportForm, EventImportForm
from places.forms import PlaceImportForm, PointImportForm, CityImportForm
from prices.forms import PriceImportForm
import importer.api.eventful.utils as utils

class EventfulBaseAdaptor(BaseAdaptor):
    source_name = 'eventful'


class PriceAdaptor(EventfulBaseAdaptor):
    model_form = PriceImportForm
    fields = ['occurrence', 'quantity']
    form_data_map = {'occurrence': 'occurrence',
                     'quantity': 'quantity'
    }

    def adapt_form_data(self, data, form_data):
        form_data['units'] = 'dollars'
        return form_data


class CityAdaptor(EventfulBaseAdaptor):
    model_form = CityImportForm
    fields = ['city', 'state']
    form_data_map = {'city': 'city', 'state': 'region'}


class PointAdaptor(EventfulBaseAdaptor):
    model_form = PointImportForm
    fields = ['latitude', 'longitude', 'address']
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
    slave_adaptors = {'point': PointAdaptor}
    fields = ['title', 'point']
    form_data_map = {
        'description': '__kwiqet/venue_details/description',
        'title': '__kwiqet/venue_details/name',
        'url': '__kwiqet/venue_details/url',
        }
    file_data_map = {'image': '__kwiqet/venue_images'}


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


class OccurrenceAdaptor(EventfulBaseAdaptor):
    model_form = OccurrenceImportForm
    fields = ['event', 'start_date', 'place', 'start_time']
    slave_adaptors = {'place': PlaceAdaptor}
    slave_adaptors_o2m = {'o2m_prices': PriceAdaptor}
    form_data_map = {
        'event': 'event',
        'start_time': 'start_time',
        'start_date': 'start_date',
        'end_date': 'end_date',
        'end_time': 'end_time',
    }
    o2m_default_field = 'occurrence'

    def __init__(self):
        super(OccurrenceAdaptor, self).__init__()

    def o2m_prices(self, data):
        return utils.expand_prices(data)


class EventAdaptor(EventfulBaseAdaptor):
    model_form = EventImportForm
    fields = ['xid', ]
    img_dict_key = 'image_local'
    slave_adaptors_o2m = {'o2m_occurrences': OccurrenceAdaptor}
    form_data_map = {
        'xid': 'id',
        'title': 'title',
        'description': 'description',
        'url': 'url',
        'image_url': 'image/url'
    }
    file_data_map = {'image': '__kwiqet/event_images'}
    o2m_default_field = 'event'

    def __init__(self):
        super(EventAdaptor, self).__init__()
        self.external_category_adaptor = CategoryAdaptor()

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
                    created, external_category = self.external_category_adaptor.parse(category_data)
                    if external_category:
                        external_category_ids.append(external_category.id)

        form_data['external_categories'] = external_category_ids
        return form_data

    def o2m_occurrences(self, raw_data):
        start_datetimes, duration, is_all_day = utils.temporal_parser.occurrences(raw_data)
        for start_datetime in start_datetimes:
            raw_data['start_date'] = start_datetime.date()
            raw_data['start_time'] = start_datetime.time()
            if duration:
                end_datetime = start_datetime + duration
                raw_data['end_date'] = end_datetime.date()
                raw_data['end_time'] = end_datetime.time()
            yield raw_data

    def post_adapt(self, data, instance):
        event = instance
        # FIXME ugly sanity check
        occurrence_count = event.occurrences.count()
        if not occurrence_count:
            self.logger.warn('Dropping Event: no parsable occurrences')
            event.delete()
