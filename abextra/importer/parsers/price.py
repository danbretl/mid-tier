from importer.parsers.base import BaseParser
from prices.forms import PriceImportForm

class PriceParser(BaseParser):
    model_form = PriceImportForm
    fields = ['occurrence', 'quantity']
    update_fields = ['remark', 'units']

    def parse_form_data(self, data, form_data):
        form_data['occurrence'] = data.occurrence
        form_data['quantity'] = data.quantity
        form_data['remark'] = data.get('remark')
        form_data['units'] = data.get('units', 'dollar')
        return form_data
