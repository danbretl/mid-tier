from django.template.defaultfilters import slugify
from importer.consumer import ScrapeFeedConsumer
from places.forms import CityImportForm
from places.models import City

class BaseParser(object):
    def __init__(self):
        self.model = self.model_form._meta.model
        self.cache = {}

    def parse(self, obj_dict):
        form_data = self.parse_form_data()
        try:
            instance = self.model.objects.get(**form_data)
        except self.model.DoesNotExist:
            form = self.model_form(form_data)
            # this will raise a ValueError, if not valid
            instance = form.save(commit=False)
        return instance

    def parse_form_data(self):
        raise NotImplementedError()

# class LocationParser(object):
#     def parse_form_data(self):
#         city = self.parse_city()
# 
#     def parse_city(self):

class CityParser(BaseParser):
    model_form = CityImportForm

    def parse_form_data(self):
        city, state = location['city'], location['state']
        slug = slugify(u'-'.join((city, state)))
        return dict(city=city, state=state, slug=slug)

consumer = ScrapeFeedConsumer()
for location in consumer.locations:
    city_parser = CityParser(location)
    print city_parser.parse()
