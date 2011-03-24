from django.template.defaultfilters import slugify
from importer.consumer import ScrapeFeedConsumer
from places.forms import CityImportForm
from places.models import City

class BaseParser(object):
    def __init__(self, obj_dict):
        self.obj_dict = obj_dict

    def parse(self):
        form_data = self.parse_form_data()
        form = self.model_form(data=form_data)
        if form.is_valid():
            return form.instance

    def parse_form_data(self):
        raise NotImplementedError()

class LocationParser(object):
    def parse_form_data(self):
        return self.obj_dict

    def parse_city(self):
        city, state = location['city'], location['state']
        slug = slugify(u'-'.join((city, state)))
        form_data = dict(city=city, state=state, slug=slug)

        try:
            city = City.objects.get(**form_data)
        except City.DoesNotExist:
            form = CityImportForm(form_data)
        else:
            form = CityImportForm(form_data, instance=city)

        if form.is_valid():
            form.save()

consumer = ScrapeFeedConsumer()
for location in consumer.locations:
    parse_city(location)
