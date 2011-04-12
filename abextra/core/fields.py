from django import forms
from django.contrib.localflavor.us.forms import USPhoneNumberField

class USPhoneNumberFieldSoftFail(USPhoneNumberField):
    def clean(self, value):
        try:
            cleaned_value = super(USPhoneNumberFieldSoftFail, self).clean(value)
        except forms.ValidationError:
            cleaned_value = u''
        return cleaned_value
