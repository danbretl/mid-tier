import os
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from importer.base import BaseParser
from events.forms import CategoryImportForm
from places.forms import PlaceImportForm, PointImportForm, CityImportForm

class CityParser(BaseParser):
    model_form = CityImportForm
    fields = ['city', 'state']

    def parse_form_data(self, data):
        form_data, file_data = {}, {}
        form_data['city'] = data['city']
        form_data['state'] = data['state']
        return form_data, file_data

class PointParser(BaseParser):
    model_form = PointImportForm
    fields = ['latitude', 'longitude', 'address']
    city_parser = CityParser()

    def parse_form_data(self, data):
        form_data, file_data = {}, {}
        form_data['latitude'] = data['latitude']
        form_data['longitude'] = data['longitude']
        form_data['address'] = data['address']
        form_data['zip'] = data['zipcode']
        form_data['country'] = 'US'

        created, city = self.city_parser.parse(data)
        if city:
            form_data['city'] = city.id

        return form_data, {}

class PlaceParser(BaseParser):
    model_form = PlaceImportForm
    fields = ['title', 'point']
    point_parser = PointParser()

    def parse_form_data(self, data):
        form_data, file_data = {}, {}

        created, point = self.point_parser.parse(data)
        if point:
            form_data['point'] = point.id

        form_data['title'] = data['title']
        form_data['phone'] = data['phone']

        url = data.get('url')
        if url:
            form_data['url'] = url

        images = data.get('images')
        if images:
            image = images[0]
            form_data['image_url'] = image['url']

            path = os.path.join(settings.SCRAPE_IMAGES_PATH, image['path'])
            with open(path, 'rb') as f:
                file_data['file'] = SimpleUploadedFile(os.path.split(f.name)[1], f.read())

        return form_data, file_data