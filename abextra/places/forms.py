from django import forms
from django.contrib.localflavor.us import forms as us_forms
from django.template.defaultfilters import slugify
from places.models import Place, Point, City
from core.fields import USPhoneNumberFieldSoftFail

# ==============
# = Base Forms =
# ==============
class PlaceForm(forms.ModelForm):
    phone = us_forms.USPhoneNumberField(required=False)
    class Meta:
        model = Place

class PointForm(forms.ModelForm):
    class Meta:
        model = Point

class CityForm(forms.ModelForm):
    state = us_forms.USStateField()
    class Meta:
        model = City

# ================
# = Import Forms =
# ================
class PlaceImportForm(PlaceForm):
    slug = forms.SlugField(required=False)
    status = forms.TypedChoiceField(empty_value=1, coerce=int, required=False)
    phone = USPhoneNumberFieldSoftFail(required=False)

    def clean_slug(self):
        title = self.cleaned_data['title']
        return slugify(title)[:50]

class PointImportForm(PointForm):
    pass

class CityImportForm(CityForm):
    slug = forms.SlugField(required=False)

    def clean_slug(self):
        city = self.cleaned_data['city']
        state = self.cleaned_data['state']
        return slugify(u'-'.join((city, state)))[:50]
