from django import forms
from django.contrib.localflavor.us import forms as us_forms
from django.template.defaultfilters import slugify
from pygeocoder import Geocoder
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
    zip = us_forms.USZipCodeField(required=False)

    _ZIPCODE_CACHE = {}

    def clean_zip(self):
        zipcode = self.cleaned_data.get('zip')
        lat_lng = tuple(map(self.cleaned_data.get, ('latitude', 'longitude')))

        # attempt to reverse geocode the zipcode
        if not zipcode and all(lat_lng):
            if not self._ZIPCODE_CACHE.has_key(lat_lng):
                results = Geocoder.reverse_geocode(*lat_lng)
                self._ZIPCODE_CACHE[lat_lng] = results[0].postal_code
            zipcode = self._ZIPCODE_CACHE.get(lat_lng)

        # if no zipcode still, fail this thing
        if not zipcode:
            raise forms.ValidationError('zipcode was not provided, nor geocoded')

        return zipcode


class CityImportForm(CityForm):
    slug = forms.SlugField(required=False)

    def clean_slug(self):
        city = self.cleaned_data['city']
        state = self.cleaned_data['state']
        return slugify(u'-'.join((city, state)))[:50]
