import os
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from importer.parsers.base import BaseParser
from importer.parsers.locations import PlaceParser
from events.forms import OccurrenceImportForm, EventImportForm

class OccurrenceParser(BaseParser):
    model_form = OccurrenceImportForm
    fields = ['event', 'start_date']
    place_parser = PlaceParser()

    def parse_form_data(self, data, form_data):
        form_data['event'] = data.get('event')

        form_data['start_date'] = data.get('start_date')
        form_data['end_date'] = data.get('end_date')
        form_data['start_time'] = data.get('start_time')
        form_data['end_time'] = data.get('end_time')

        created, place = self.place_parser.parse(data.get('location', {}))
        form_data['place'] = place.id if place else None

        return form_data

class EventParser(BaseParser):
    model_form = EventImportForm
    fields = ['xid',]
    occurrence_parser = OccurrenceParser()

    def parse_form_data(self, data, form_data):
        form_data['xid'] = data.get('guid')
        form_data['title'] = data.get('title')
        form_data['description'] = data.get('description').encode('unicode-escape')
        # submitted_by = models.ForeignKey(User, blank=True, null=True) # should always be Importer or some such
        # created = models.DateTimeField(auto_now_add=True)
        # modified = models.DateTimeField(auto_now=True)
        form_data['url'] = data.get('url')
        # image = ImageField(upload_to='event_images', blank=True, null=True)
        # image_url = models.URLField(verify_exists=False, max_length=300, blank=True)
        # video_url = models.URLField(verify_exists=False, max_length=200, blank=True)
        form_data['concrete_category'] = 2
        # categories = models.ManyToManyField(Category, related_name='events_abstract', verbose_name=_('abstract categories'))
        # is_active = models.BooleanField(default=True)

        return form_data

    def post_parse(self, data, instance):
        for occurrence_data in data.occurrences:
            occurrence_data['event'] = instance.id
            print self.occurrence_parser.parse(occurrence_data)
