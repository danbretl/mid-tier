from django import forms
from django.template.defaultfilters import slugify

from events.models import Category


class CategoryAdminForm(forms.ModelForm):
    class Meta:
        model = Category

    def save(self, commit=True):
        self.instance.slug = slugify(self.cleaned_data['title'])
        # get category_type from the parent if provided else it's 'OTHER'
        parent = self.cleaned_data.get('parent')
        self.instance.category_type = parent.category_type if parent else 'O'
        return super(CategoryAdminForm, self).save(commit=commit)
