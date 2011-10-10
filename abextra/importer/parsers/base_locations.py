from importer.parsers.base import BaseParser
from places.forms import PlaceImportForm, PointImportForm, CityImportForm

class BaseCityParser(BaseParser):
    model_form = CityImportForm
    fields = ['city', 'state']

    def parse_form_data(self, data, form_data):
        raise NotImplementedError()

class PointParser(BaseParser):
    model_form = PointImportForm
    fields = ['latitude', 'longitude', 'address']
    city_parser = CityParser()

    def parse_form_data(self, data, form_data):
        raise NotImplementedError()

class PlaceParser(BaseParser):
    model_form = PlaceImportForm
    fields = ['title', 'point']
    point_parser = PointParser()

    def parse_form_data(self, data, form_data):
        raise NotImplementedError()

