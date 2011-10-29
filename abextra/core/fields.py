from django import forms
from django.db import models
from django.contrib.localflavor.us.forms import USPhoneNumberField
from south.modelsinspector import add_introspection_rules
from BeautifulSoup import BeautifulSoup, Comment
from core.utils import html_sanitize

class USPhoneNumberFieldSoftFail(USPhoneNumberField):
    def clean(self, value):
        try:
            cleaned_value = super(USPhoneNumberFieldSoftFail, self).clean(value)
        except forms.ValidationError:
            cleaned_value = u''
        return cleaned_value


class HtmlSanitizedCharField(forms.CharField):
    widget=forms.widgets.Textarea()

#    valid_tags = 'p i strong b u a h1 h2 h3 pre br img'.split()
    valid_tags = []
    valid_attrs = 'href src'.split()

    def clean(self, value):
        """Cleans non-allowed HTML from the input."""
        value = super(HtmlSanitizedCharField, self).clean(value)
        return html_sanitize(value, self.valid_tags, self.valid_attrs)

class VectorField(models.Field):
    def __init__(self, *args, **kwargs):
        kwargs['null'] = True
        kwargs['editable'] = False
        kwargs['serialize'] = False
        super(VectorField, self).__init__(*args, **kwargs)

    def db_type(self, connection=None):
        return 'tsvector'

add_introspection_rules([], [r'^core\.fields\.VectorField'])
