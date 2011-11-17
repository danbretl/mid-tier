from django import forms
from django.contrib.gis import geos
from django.contrib.gis.forms import GeometryField
from django.contrib.localflavor.us import forms as us_forms
from django.template.defaultfilters import slugify
from pygeocoder import Geocoder
from core.forms import ImportFormMux
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
        exclude = ('slug')

# ================
# = Import Forms =
# ================
class PlaceImportForm(PlaceForm):
    slug = forms.SlugField(required=False, max_length=PlaceForm._meta.model._meta.get_field('slug').max_length)
    phone = USPhoneNumberFieldSoftFail(required=False)
    status = forms.TypedChoiceField(empty_value=1, coerce=int, required=False)

    def clean(self):
        cleaned_data = super(PlaceImportForm, self).clean()
        title = cleaned_data.get('title')
        if not title:
            raise forms.ValidationError('Slug field requires title')
        slug_value = slugify(title)[:50]
        cleaned_data['slug'] = self.fields['slug'].clean(slug_value)
        return cleaned_data


class PointImportForm(PointForm):
    zip = us_forms.USZipCodeField(required=False)
    geometry = GeometryField(geom_type='POINT', srid=4326, required=False)
    latitude = forms.FloatField(min_value=-90, max_value=90)
    longitude = forms.FloatField(min_value=-180, max_value=180)

    _ZIPCODE_CACHE = {}

    def clean(self):
        cleaned_data = super(PointImportForm, self).clean()
        lat, lon = map(cleaned_data.get, ('latitude', 'longitude'))

        # point geometry
        geometry = cleaned_data.get('geometry')
        if not geometry:
            if not all((lat, lon)):
                raise forms.ValidationError('Geometry fields require latitude and longitude')
            geometry_field = self.fields['geometry']
            pnt = geos.Point(lon, lat, srid=geometry_field.srid)
            cleaned_data['geometry'] = geometry_field.clean(pnt)

        # zipcode geocode
        zipcode = cleaned_data.get('zip')
        if not zipcode:
            if not all((lat, lon)):
                raise forms.ValidationError('Zipcode fields require latitude and longitude')
            key = (lat, lon)
            if not self._ZIPCODE_CACHE.has_key(key):
                results = Geocoder.reverse_geocode(lat=lat, lng=lon)
                self._ZIPCODE_CACHE[key] = results[0].postal_code
            zipcode = self._ZIPCODE_CACHE.get(key)
            cleaned_data['zip'] = self.fields['zip'].clean(zipcode)

        return cleaned_data


class CityImportForm(ImportFormMux, CityForm):
    pass
