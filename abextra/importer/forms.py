from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from importer import ImportFormMetaClass
from importer.models import ExternalCategory
from events.models import Category, Source

class ExternalCategoryForm(forms.ModelForm):
    class Meta:
        model = ExternalCategory

class ExternalCategoryAdminForm(ExternalCategoryForm):
    concrete_category = forms.ModelChoiceField(
        queryset=Category.concrete.all().order_by('title'),
        empty_label="Select an internal category",
        required=False
    )
    abstract_categories = forms.ModelMultipleChoiceField(
        queryset=Category.abstract.all(),
        widget=FilteredSelectMultiple(u'abstract categories', is_stacked=False),
        required=False
    )

class ExternalCategoryImportForm(ExternalCategoryForm):
    __metaclass__ = ImportFormMetaClass

    source = forms.ModelChoiceField(
        queryset=Source.objects.all(),
        cache_choices=True,
        to_field_name='name'
    )
