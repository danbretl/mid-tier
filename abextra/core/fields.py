from django import forms
from django.db import models
from django.contrib.localflavor.us.forms import USPhoneNumberField
from south.modelsinspector import add_introspection_rules

class USPhoneNumberFieldSoftFail(USPhoneNumberField):
    def clean(self, value):
        try:
            cleaned_value = super(USPhoneNumberFieldSoftFail, self).clean(value)
        except forms.ValidationError:
            cleaned_value = u''
        return cleaned_value


class VectorField(models.Field):
    def __init__(self, *args, **kwargs):
        kwargs['null'] = True
        kwargs['editable'] = False
        kwargs['serialize'] = False
        super(VectorField, self).__init__(*args, **kwargs)

    def db_type(self, connection=None):
        return 'tsvector'

add_introspection_rules([], [r'^core\.fields\.VectorField'])
