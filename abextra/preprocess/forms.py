from django import forms

from preprocess.models import ExternalCategory
from events.models import Category

class ExternalCategoryAdminForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        empty_label="Select an internal category",
        required=False
    )

    class Meta:
        model = ExternalCategory
