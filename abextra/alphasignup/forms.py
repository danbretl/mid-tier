from django import forms
from userena.forms import SignupFormOnlyEmail

from accounts.models import UserProfile

class AlphaSignupForm(SignupFormOnlyEmail):
    iphone_user = forms.BooleanField()
    device_platform = forms.TypedChoiceField(choices=UserProfile.DEVICE_PLATFORM_CHOICES)
    # is_nyc_resident = models.BooleanField(default=False)

    # def __init__(self, *args, **kwargs):
    #     super(AlphaSignupForm, self).__init__(*args, **kwargs)
    #     del self.fields['password1']
    #     del self.fields['password2']

    # def save(self):
    #     """ Generate a random username before falling back to parent signup form """
    #     while True:
    #         username = sha_constructor(str(random.random())).hexdigest()[:5]
    #         try:
    #             User.objects.get(username__iexact=username)
    #         except User.DoesNotExist: break
    # 
    #     self.cleaned_data['username'] = username
    #     return super(SignupFormOnlyEmail, self).save()
    