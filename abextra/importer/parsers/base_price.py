from importer.parsers.base import BaseParser
from prices.forms import PriceImportForm

class PriceParser(BaseParser):
    model_form = PriceImportForm
    fields = ['occurrence', 'quantity']

    def parse_form_data(self, data, form_data):
        raise NotImplementedError()
