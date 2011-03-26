from importer.base import BaseParser
from events.forms import CategoryImportForm
from places.forms import PlaceImportForm, PointImportForm, CityImportForm

class CityParser(BaseParser):
    model_form = CityImportForm
    fields = ['city', 'state']

    def parse_form_data(self, data):
        form_data = {}
        form_data['city'] = data['city']
        form_data['state'] = data['state']
        return form_data

class PointParser(BaseParser):
    model_form = PointImportForm
    fields = ['latitude', 'longitude', 'address']
    city_parser = CityParser()

    def parse_form_data(self, data):
        form_data = {}
        form_data['latitude'] = data['latitude']
        form_data['longitude'] = data['longitude']
        form_data['address'] = data['address']
        form_data['zip'] = data['zipcode']
        form_data['city'] = self.city_parser.parse(data).id
        form_data['country'] = 'US'
        return form_data
