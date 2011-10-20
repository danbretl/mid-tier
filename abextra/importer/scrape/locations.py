from importer.parsers.base import BaseAdapter
from places.forms import PlaceImportForm, PointImportForm, CityImportForm

class CityAdapter(BaseAdapter):
    model_form = CityImportForm
    fields = ['city', 'state']

    def adapt_form_data(self, data, form_data):
        form_data['city'] = data.get('city')
        form_data['state'] = data.get('state')
        #TODO: Try and get this from geocoding information.
        return form_data

class PointAdapter(BaseAdapter):
    model_form = PointImportForm
    fields = ['latitude', 'longitude', 'address']
    city_parser = CityAdapter()

    def adapt_form_data(self, data, form_data):
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

class PlaceAdapter(BaseAdapter):
    model_form = PlaceImportForm
    fields = ['title', 'point']
    point_parser = PointAdapter()

    def adapt_form_data(self, data, form_data):
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

