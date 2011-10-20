from importer.parsers.base import BaseAdapter
from prices.forms import PriceImportForm

class PriceAdapter(BaseAdapter):
    model_form = PriceImportForm
    fields = ['occurrence', 'quantity']

    def adapt_form_data(self, data, form_data):
        raise NotImplementedError()
