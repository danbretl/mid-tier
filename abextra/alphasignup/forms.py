from django import forms
from django.utils.translation import ugettext_lazy as _

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

class AlphaQuestionnaireForm(forms.ModelForm):
    class Meta:
        model = AlphaQuestionnaire

class AlphaQuestionnaireAdminForm(AlphaQuestionnaireForm):
    pass