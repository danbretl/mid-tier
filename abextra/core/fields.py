from django import forms
from django.db import models
from django.contrib.localflavor.us.forms import USPhoneNumberField
from south.modelsinspector import add_introspection_rules
from BeautifulSoup import BeautifulSoup, Comment

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
        soup = BeautifulSoup(value)
        for comment in soup.findAll(text=lambda text: isinstance(text, Comment)):
            comment.extract()
        for tag in soup.findAll(True):
            if tag.name not in self.valid_tags:
                tag.hidden = True
#            tag.attrs = [(attr, val) for attr, val in tag.attrs if attr in self.valid_attrs]
        return soup.renderContents().decode('utf8')


class VectorField(models.Field):
    def __init__(self, *args, **kwargs):
        kwargs['null'] = True
        kwargs['editable'] = False
        kwargs['serialize'] = False
        super(VectorField, self).__init__(*args, **kwargs)

    def db_type(self, connection=None):
        return 'tsvector'

add_introspection_rules([], [r'^core\.fields\.VectorField'])
