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
        form_data['title'] = data.get('title').encode('unicode-escape')
        form_data['description'] = data.get('description').encode('unicode-escape')
        form_data['url'] = data.get('url')

        images = data.get('images')
        if images:
            image = images[0]
            form_data['image_url'] = image['url']

        return form_data

    def post_parse(self, data, instance):
        for occurrence_data in data.occurrences:
            occurrence_data['event'] = instance.id
            self.occurrence_parser.parse(occurrence_data)
