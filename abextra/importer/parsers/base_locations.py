from importer.parsers.base import BaseAdapter
from places.forms import PlaceImportForm, PointImportForm, CityImportForm

class BaseCityAdapter(BaseAdapter):
    model_form = CityImportForm
    fields = ['city', 'state']

    def adapt_form_data(self, data, form_data):
        raise NotImplementedError()

class PointAdapter(BaseAdapter):
    model_form = PointImportForm
    fields = ['latitude', 'longitude', 'address']
    city_parser = CityParser()

    def adapt_form_data(self, data, form_data):
        raise NotImplementedError()

class PlaceAdapter(BaseAdapter):
    model_form = PlaceImportForm
    fields = ['title', 'point']
    point_parser = PointAdapter()

    def adapt_form_data(self, data, form_data):
        raise NotImplementedError()

