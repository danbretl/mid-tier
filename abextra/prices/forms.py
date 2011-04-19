from django import forms
from prices.models import Price

class PriceForm(forms.ModelForm):
    class Meta:
        model = Price

class PriceImportForm(PriceForm):
    pass