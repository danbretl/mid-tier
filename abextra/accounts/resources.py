from allauth.account.forms import SignupForm
from django.contrib.auth.models import User, Group
from django import forms
from django.utils.translation import ugettext_lazy as _

from accounts.models import UserProfile
from tastypie.authorization import DjangoAuthorization
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.http import HttpBadRequest, HttpCreated
from tastypie.resources import ModelResource
from tastypie.utils import dict_strip_unicode_keys
from tastypie.utils.mime import build_content_type
from tastypie.validation import FormValidation

from api.authentication import ConsumerAuthentication

# ========
# = User =
# ========
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
        UserProfile.objects.create(user=new_user)
        device_user_group = Group.objects.get(id=5)
        new_user.groups.add(device_user_group)


class UserResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        list_allowed_methods = ('post',)
        detail_allowed_methods = ()
        authentication = ConsumerAuthentication()
        authorization = DjangoAuthorization()
        validation = FormValidation(form_class=SignupFormFirstLastName)
        resource_name = 'registration'

    def is_valid(self, bundle, request=None):
        """Overriden to perform validation and persistence in one step"""
        form = self._meta.validation.form_class(data=bundle.data)

        # validation
        if form.is_valid():
            new_user = form.save()
            request.user = new_user
            request.user_created = True

        # error handling
        else:
            if request:
                desired_format = self.determine_format(request)
            else:
                desired_format = self._meta.default_format

            serialized = self.serialize(request, form.errors, desired_format)
            response = HttpBadRequest(content=serialized, content_type=build_content_type(desired_format))
            raise ImmediateHttpResponse(response=response)

    def obj_create(self, bundle, request=None, **kwargs):
        """Overridden to cancel persistence, since it's done in `is_valid`"""
        return bundle

    def post_list(self, request, **kwargs):
        """Overridden to inject ApiKey into response content"""
        response = super(UserResource, self).post_list(request, **kwargs)
        if request:
            user, created = getattr(request, 'user', None), getattr(request, 'user_created', None)
            if user and created and user.api_key:
                response.content = user.api_key.key
        return response

# ==================
# = Password Reset =
# ==================
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.views import password_reset

class PasswordResetResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        list_allowed_methods = ('post',)
        detail_allowed_methods = ()
        authentication = ConsumerAuthentication()
        authorization = DjangoAuthorization()
        validation = FormValidation(form_class=PasswordResetForm)

    def post_list(self, request, **kwargs):
        deserialized = self.deserialize(
            request, request.raw_post_data,
            format=request.META.get('CONTENT_TYPE', 'application/json')
        )
        bundle = self.build_bundle(data=dict_strip_unicode_keys(deserialized))
        self.is_valid(bundle, request)
        post = request.POST.copy()
        post.update(bundle.data)
        request.POST = post
        request._dont_enforce_csrf_checks = True
        response = password_reset(request)
        return HttpCreated(location=response['location'])
