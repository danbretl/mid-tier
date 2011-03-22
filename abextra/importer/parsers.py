from importer import parser_registry
from parser_base import BaseParser
from events.forms import CategoryImportForm

class BaseParser(object):
    def __init__(self, obj_dict):
        self.obj_dict = obj_dict

    def parse(self):
        form_data = self.parse_form_data()
        form = self.model_form(data=form_data)
        import ipdb; ipdb.set_trace()
        if form.is_valid():
            return form.instance

    def parse_form_data(self):
        raise NotImplementedError()


class CategoryParser(BaseParser):
    model_form = CategoryImportForm
    def parse_form_data(self):
        return self.obj_dict
parser_registry.register('category', CategoryParser)


class EventParser(BaseParser):
    def parse_form_data(self):
        return self.obj_dict
parser_registry.register('event', EventParser)


class OccurrenceParser(BaseParser):
    def parse_form_data(self):
        return self.obj_dict
parser_registry.register('occurrence', OccurrenceParser)


class LocationParser(BaseParser):
    def parse_form_data(self):
        return self.obj_dict
parser_registry.register('location', LocationParser)
