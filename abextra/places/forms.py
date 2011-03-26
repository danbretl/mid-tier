from django import forms
from django.contrib.localflavor.us import forms as us_forms
from django.template.defaultfilters import slugify
from places.models import Place, Point, City

class PlaceForm(forms.ModelForm):
    phone = us_forms.USPhoneNumberField()
    class Meta:
        model = Place

class PointForm(forms.ModelForm):
    class Meta:
        model = Point

class CityForm(forms.ModelForm):
    state = us_forms.USStateField()
    slug = forms.SlugField(required=False)

    def clean_slug(self):
        city = self.cleaned_data['city']
        state = self.cleaned_data['state']
        return slugify(u'-'.join((city, state)))

    class Meta:
        model = City

class PlaceImportForm(PlaceForm):
    pass

class PointImportForm(PointForm):
    pass

class CityImportForm(CityForm):
    pass
