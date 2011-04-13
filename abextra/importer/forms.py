from django import forms

from importer.models import ExternalCategory
from events.models import Category, Source

class ExternalCategoryForm(forms.ModelForm):
    class Meta:
        model = ExternalCategory

class ExternalCategoryAdminForm(ExternalCategoryForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        empty_label="Select an internal category",
        required=False
    )

class ExternalCategoryImportForm(ExternalCategoryForm):
    source = forms.ModelChoiceField(
        queryset=Source.objects.all(),
        cache_choices=True
    )
