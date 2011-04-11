import os
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from importer.parsers.base import BaseParser
from places.forms import PlaceImportForm, PointImportForm, CityImportForm

class CityParser(BaseParser):
    model_form = CityImportForm
    fields = ['city', 'state']

    def parse_form_data(self, data, form_data):
        form_data['city'] = data.get('city')
        form_data['state'] = data.get('state')
        #TODO: Try and get this from geocoding information.
        return form_data

class PointParser(BaseParser):
    model_form = PointImportForm
    fields = ['latitude', 'longitude', 'address']
    city_parser = CityParser()

    def parse_form_data(self, data, form_data):
        # Also possible, get an address from lat long?
        # Keeping the address compulsory for now for sanity.
        form_data['address'] = data.get('address')
        form_data['latitude'] = data.get('latitude')
        form_data['longitude'] = data.get('longitude')
        form_data['zip'] = data.get('zipcode')
        form_data['country'] = 'US'

        created, city = self.city_parser.parse(data)
        if city:
            form_data['city'] = city.id
        return form_data

class PlaceParser(BaseParser):
    model_form = PlaceImportForm
    fields = ['title', 'point']
    point_parser = PointParser()

    def parse_form_data(self, data, form_data):
        created, point = self.point_parser.parse(data)
        if point:
            form_data['point'] = point.id

        form_data['title'] = data.get('title')
        form_data['phone'] = data.get('phone')
        form_data['url'] = data.get('url')

        images = data.get('images')
        if images:
            image = images[0]
            form_data['image_url'] = image['url']
        return form_data

    def parse_file_data(self, data, file_data):
        images = data.get('images')
        if images:
            image = images[0]
            path = os.path.join(settings.SCRAPE_IMAGES_PATH, image['path'])
            with open(path, 'rb') as f:
                filename = os.path.split(f.name)[1]
                file_data['image'] = SimpleUploadedFile(filename, f.read())
        return file_data

