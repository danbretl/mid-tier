from allauth.account.forms import SignupForm
from django import forms
from django.contrib.auth.models import Group
from django.utils.translation import ugettext_lazy as _

class SignupFormFirstLastName(SignupForm):
    first_name = forms.CharField(label=_(u'First name'), max_length=30, required=True)
    last_name = forms.CharField(label=_(u'Last name'), max_length=30, required=True)

    def __init__(self, *args, **kwargs):
        super(SignupFormFirstLastName, self).__init__(*args, **kwargs)
        self.fields.keyOrder.extend(['first_name', 'last_name'])

    def after_signup(self, user, **kwargs):
        super(SignupFormFirstLastName, self).after_signup(user, **kwargs)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
        device_user_group = Group.objects.get(id=5)
        user.groups.add(device_user_group)
