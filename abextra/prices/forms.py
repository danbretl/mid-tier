from django import forms
from prices.models import Price
from importer import ImportFormMetaClass


class PriceForm(forms.ModelForm):
    class Meta:
        model = Price


class PriceImportForm(PriceForm):
    __metaclass__ = ImportFormMetaClass
