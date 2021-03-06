from importer.parsers.base import BaseAdapter
from importer.parsers.locations import PlaceAdapter
from importer.parsers.price import PriceAdapter
from importer.forms import ExternalCategoryImportForm
from events.forms import OccurrenceImportForm, EventImportForm
from events.models import Source, EventSummary
from events.utils import CachedCategoryTree

class ExternalCategoryAdapter(BaseAdapter):
    model_form = ExternalCategoryImportForm
    fields = ['source', 'xid']

    def adapt_form_data(self, data, form_data):
        source = Source.objects.get(name=data.source)
        form_data['source'] = source.id
        form_data['xid'] = data.get('guid')
        form_data['name'] = data.get('title')

        return form_data

class OccurrenceAdapter(BaseAdapter):
    model_form = OccurrenceImportForm
    fields = ['event', 'start_date', 'place', 'start_time']
    place_parser = PlaceAdapter()
    price_parser = PriceAdapter()

    def adapt_form_data(self, data, form_data):
        form_data['event'] = data.get('event')

        form_data['start_date'] = data.get('start_date')
        form_data['end_date'] = data.get('end_date')
        form_data['start_time'] = data.get('start_time')
        form_data['end_time'] = data.get('end_time')

        created, place = self.place_parser.parse(data.get('location', {}))
        form_data['place'] = place.id if place else None

        return form_data

    def post_adapt(self, data, instance):
        occurrence = instance

        # prices
        for price_data in data.prices:
            price_data['occurrence'] = occurrence.id
            self.price_parser.parse(price_data)

class EventAdapter(BaseAdapter):
    model_form = EventImportForm
    fields = ['xid',]
    occurrence_parser = OccurrenceAdapter()
    external_category_parser = ExternalCategoryAdapter()

    def __init__(self, *args, **kwargs):
        super(EventAdapter, self).__init__(*args, **kwargs)
        self.ctree = CachedCategoryTree()

    def adapt_form_data(self, data, form_data):
        form_data['source'] = data.get('source')
        form_data['xid'] = data.get('guid')
        form_data['title'] = data.get('title')
        form_data['description'] = data.get('description')
        form_data['url'] = data.get('url')
        form_data['popularity_score'] = data.get('popularity_score')
        categories = data.get('categories') or []
        external_category_ids = []
        for category_data in categories:
            created, external_category = self.external_category_parser.parse(category_data)
            external_category_ids.append(external_category.id)
        form_data['external_categories'] = external_category_ids

        images = data.get('images')
        if images:
            image = images[0]
            form_data['image_url'] = image['url']

        return form_data

    def post_adapt(self, data, instance):
        event = instance

        # occurrences
        for occurrence_data in data.occurrences:
            occurrence_data['event'] = event.id
            self.occurrence_parser.parse(occurrence_data)

        # sanity check  FIXME ugly
        occurrence_count = event.occurrences.count()
        if not occurrence_count:
            self.logger.warn('Dropping Event: no parsable occurrences')
            event.delete()
            return

        # event summary
        EventSummary.objects.for_event(event, self.ctree)
