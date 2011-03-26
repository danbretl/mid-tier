from collections import namedtuple
from events.forms import CategoryImportForm
from places.forms import PlaceImportForm, PointImportForm, CityImportForm

class BaseParser(object):
    def __init__(self):
        self.model = self.model_form._meta.model
        self.key_tuple = namedtuple('key_tuple', self.fields)
        self.cache = {}

    def parse(self, data):
        form_data = self.parse_form_data(data)
        key = self.cache_key(form_data)
        instance = self.cache.get(key)
        if not instance:
            try:
                instance = self.model.objects.get(**key._asdict())
                self.cache[key] = instance
            except self.model.DoesNotExist:
                form = self.model_form(form_data)
                # this will raise a ValueError, if not valid
                instance = form.save(commit=True)
        return instance

    def cache_key(self, form_data):
        return self.key_tuple(
            **dict((f, form_data[f]) for f in self.fields if form_data.has_key(f))
        )

    def parse_form_data(self, obj_dict):
        raise NotImplementedError()

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
