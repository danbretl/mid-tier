from importer.parsers.base import BaseAdapter
from prices.forms import PriceImportForm

class PriceAdapter(BaseAdapter):
    model_form = PriceImportForm
    fields = ['occurrence', 'quantity']

    def adapt_form_data(self, data, form_data):
        form_data['occurrence'] = data.occurrence
        form_data['quantity'] = data.quantity
        form_data['remark'] = data.get('remark')
        form_data['units'] = data.get('units', 'dollar')
        return form_data
