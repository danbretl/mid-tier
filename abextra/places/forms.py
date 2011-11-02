from django import forms
from django.contrib.gis import geos
from django.contrib.gis.forms import GeometryField
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
    geometry = GeometryField(geom_type='POINT', srid=4326, required=False)
    latitude = forms.FloatField(min_value=-90, max_value=90)
    longitude = forms.FloatField(min_value=-180, max_value=180)

    _ZIPCODE_CACHE = {}

    def clean(self):
        lat, lon = map(self.cleaned_data.get, ('latitude', 'longitude'))

        # point geometry
        geometry = self.cleaned_data.get('geometry')
        if not geometry:
            geometry_field = self.fields['geometry']
            pnt = geos.Point(lon, lat, srid=geometry_field.srid)
            self.cleaned_data['geometry'] = geometry_field.clean(pnt)

        # zipcode geocode
        zipcode = self.cleaned_data.get('zip')
        if not zipcode:
            key = (lat, lon)
            if not self._ZIPCODE_CACHE.has_key(key):
                results = Geocoder.reverse_geocode(lat=lat, lng=lon)
                self._ZIPCODE_CACHE[key] = results[0].postal_code
            zipcode = self._ZIPCODE_CACHE.get(key)
            self.cleaned_data['zip'] = self.fields['zip'].clean(zipcode)

        return self.cleaned_data


class CityImportForm(CityForm):
    slug = forms.SlugField(required=False)

    def clean_slug(self):
        city = self.cleaned_data.get('city')
        state = self.cleaned_data.get('state')
        if not all((city, state)):
            raise forms.ValidationError('Both city and state are required for form')
        return slugify(u'-'.join((city, state)))[:50]
