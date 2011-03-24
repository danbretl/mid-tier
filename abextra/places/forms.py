from django import forms
from django.contrib.localflavor.us import us_forms
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
    class Meta:
        model = City

class PlaceImportForm(PlaceForm):
    pass

class PointImportForm(PointForm):
    pass

class CityImportForm(CityForm):
    pass
