from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.contrib.localflavor.us import forms as us_forms

from accounts.models import UserProfile
from alphasignup.models import AlphaQuestionnaire
from userena.forms import SignupFormOnlyEmail

class AlphaSignupForm(SignupFormOnlyEmail):
    first_name = forms.RegexField(regex=r'^[A-Za-z]+$', max_length=30,
        widget=forms.TextInput(), label=_("First Name"),
        error_messages={'invalid': _('First name must contain only letters.')})

    last_name = forms.RegexField(regex=r'^[A-Za-z\-]+$', max_length=30,
        widget=forms.TextInput(), label=_("Last Name"),
        error_messages={'invalid': _('Last name must contain only letters and hyphens.')})

    # iphone_user = forms.BooleanField()
    # device_platform = forms.TypedChoiceField(choices=UserProfile.DEVICE_PLATFORM_CHOICES)
    # is_nyc_resident = models.BooleanField(default=False)

    def __init__(self, *args, **kwargs):
        super(AlphaSignupForm, self).__init__(*args, **kwargs)
        del self.fields['password1']
        del self.fields['password2']

    def save(self):
        """ Creates a new user and account. Returns the newly created user. """
        self.cleaned_data['password1'] = None
        new_user = super(AlphaSignupForm, self).save()
        new_user.first_name = self.cleaned_data['first_name']
        new_user.last_name = self.cleaned_data['last_name']
        new_user.save()
        return new_user


from django.forms.widgets import RadioFieldRenderer
class HorizontalRadioRenderer(RadioFieldRenderer):
    """renders horizontal radio buttons"""
    def render(self):
        return mark_safe(u'\n'.join([u'%s\n' % w for w in self]))

class AlphaQuestionnaireForm(forms.ModelForm):
    zip = us_forms.USZipCodeField()
    year_of_birth = forms.IntegerField(
        widget=forms.TextInput(attrs={'size':'4'}),
        min_value = 1910, max_value=2005,
        error_messages={
            'min_value': _('No way?!?'),
            'max_value': _('Your parents are too liberal!')
        }
    )

    def __init__(self, *args, **kwargs):
        super(AlphaQuestionnaireForm, self).__init__(*args, **kwargs)
        import ipdb; ipdb.set_trace()
        self.base_fields['device_platform'].label = _('Mobile Platform')
        self.base_fields['is_usage_info_ok'].label = \
            _('May we use the data we collect from your usage in order to improve our application/future user experiences?')
        self.base_fields['is_mobile_planner'].label = \
            _('Do you frequently use mobile applications to plan outings with friends/schedule events and activities?')
        self.base_fields['is_app_dev'].label = \
            _('Are you an app developer or currently working on a mobile application?')
        self.declared_fields['zip'].label = _('Postal Code')
        self.declared_fields['year_of_birth'].label = _('Year of Birth')

    class Meta:
        model = AlphaQuestionnaire
        exclude = ('profile',)
        widgets = {
            'is_usage_info_ok': forms.RadioSelect(renderer=HorizontalRadioRenderer),
            'is_mobile_planner': forms.RadioSelect(renderer=HorizontalRadioRenderer),
            'is_app_dev': forms.RadioSelect(renderer=HorizontalRadioRenderer),
        }

# ====================
# = UserProfile Form =
# ====================
from userena.forms import EditProfileForm
class EditProfileAlphaForm(EditProfileForm):
    class Meta(EditProfileForm.Meta):
        exclude = ('user', 'privacy', 'alpha_status')