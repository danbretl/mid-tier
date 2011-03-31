from django import forms
from django.contrib.localflavor.us import forms as us_forms
from django.template.defaultfilters import slugify
from places.models import Place, Point, City

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

class PlaceImportForm(PlaceForm):
    slug = forms.SlugField(required=False)
    status = forms.TypedChoiceField(empty_value=1, coerce=int, required=False)

    def clean_phone(self):
        import ipdb; ipdb.set_trace()
        phone = self.data.get('phone', '')
        if phone:
            import ipdb; ipdb.set_trace()
            try:
                phone = self.base_fields['phone'].clean(phone)
            except forms.ValidationError:
                import ipdb; ipdb.set_trace()
                pass
        return phone

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
