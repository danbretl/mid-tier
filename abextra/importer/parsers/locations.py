import os
import re
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from importer.parsers.base import BaseParser
from places.forms import PlaceImportForm, PointImportForm, CityImportForm

class CityParser(BaseParser):
    model_form = CityImportForm
    fields = ['city', 'state']

    def parse_form_data(self, data, form_data):
        form_data['city'] = data['city']
        form_data['state'] = data['state']
        #TODO: Try and get this from geocoding information.
        return form_data

class PointParser(BaseParser):
    model_form = PointImportForm
    fields = ['latitude', 'longitude', 'address']
    city_parser = CityParser()

    def __init__(self, **kwargs):
        """
        
        Arguments:
        - `self`:
        """
        super(PointParser, self).__init__(**kwargs)
        self.zipcode_re = re.compile('\d{5,5}')
        
    def parse_form_data(self, data, form_data):
        # Also possible, get an address from lat long?
        # Keeping the address compulsory for now for sanity. 
        form_data['address'] = data['address']

        latitude = data.get('latitude')
        if latitude:        
            form_data['latitude'] = latitude
        else:
            # We could try to get lat long using geo coding here
            # Input address, Output lat, long. 
            pass

        longitude = data.get('longitude')
        if longitude:
            form_data['longitude'] = longitude
        else:
            # We could try to get lat long using geo coding here
            # Input address, Output lat, long.
            pass
 
        zipcode = data.get('zipcode')
        if zipcode:        
            form_data['zip'] = zipcode
        else:
            #check if there is a zipcode in the address.
            match = self.zipcode_re.search(data['address'])
            if match:
                form_data['zip'] = match.group(0)

            # We could also try and get zip code from lat-long
            # here if possible. 
            
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

        form_data['title'] = data['title']
        phone = data.get('phone')
        if phone:        
            form_data['phone'] = phone
        else:
            # This is a bad place to be in.
            # Find a better way to get a phone number.
            # Maybe add some flag for manually
            # adding phone numbers.
            pass

        url = data.get('url')
        if url:
            form_data['url'] = url

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

