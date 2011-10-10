from importer.parsers.base import BaseParser
from importer.parsers.locations import PlaceParser
from importer.parsers.price import PriceParser
from importer.forms import ExternalCategoryImportForm
from events.forms import OccurrenceImportForm, EventImportForm
from events.models import Source, EventSummary
from events.utils import CachedCategoryTree

class BaseExternalCategoryParser(BaseParser):
    model_form = ExternalCategoryImportForm
    fields = ['source', 'xid']

    def parse_form_data(self, data, form_data):
        raise NotImplementedError

class BaseOccurrenceParser(BaseParser):
    model_form = OccurrenceImportForm
    fields = ['event', 'start_date', 'place', 'start_time']
    place_parser = PlaceParser()
    price_parser = PriceParser()

    def parse_form_data(self, data, form_data):
        raise NotImplementedError

    def post_parse(self, data, instance):
        raise NotImplementedError

class BaseEventParser(BaseParser):
    model_form = EventImportForm
    fields = ['xid',]
    occurrence_parser = OccurrenceParser()
    external_category_parser = ExternalCategoryParser()

    def __init__(self, *args, **kwargs):
        super(EventParser, self).__init__(*args, **kwargs)
        self.ctree = CachedCategoryTree()

    def parse_form_data(self, data, form_data):
        raise NotImplementedError

    def post_parse(self, data, instance):
        raise NotImplementedError
