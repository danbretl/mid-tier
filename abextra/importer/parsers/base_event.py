from importer.parsers.base import BaseAdapter
from importer.parsers.locations import PlaceAdapter
from importer.parsers.price import PriceAdapter
from importer.forms import ExternalCategoryImportForm
from events.forms import OccurrenceImportForm, EventImportForm
from events.models import Source, EventSummary
from events.utils import CachedCategoryTree

class BaseExternalCategoryAdapter(BaseAdapter):
    model_form = ExternalCategoryImportForm
    fields = ['source', 'xid']

    def adapt_form_data(self, data, form_data):
        raise NotImplementedError

class BaseOccurrenceAdapter(BaseAdapter):
    model_form = OccurrenceImportForm
    fields = ['event', 'start_date', 'place', 'start_time']
    place_parser = PlaceAdapter()
    price_parser = PriceAdapter()

    def adapt_form_data(self, data, form_data):
        raise NotImplementedError

    def post_adapt(self, data, instance):
        raise NotImplementedError

class BaseEventAdapter(BaseAdapter):
    model_form = EventImportForm
    fields = ['xid',]
    occurrence_parser = OccurrenceParser()
    external_category_parser = ExternalCategoryParser()

    def __init__(self, *args, **kwargs):
        super(EventParser, self).__init__(*args, **kwargs)
        self.ctree = CachedCategoryTree()

    def adapt_form_data(self, data, form_data):
        raise NotImplementedError

    def post_adapt(self, data, instance):
        raise NotImplementedError
