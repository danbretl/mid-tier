from django.core.urlresolvers import resolve, Resolver404
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings
from sorl.thumbnail import get_thumbnail

from tastypie import fields
from tastypie.authentication import Authentication
from tastypie.authorization import DjangoAuthorization, Authorization
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.exceptions import ImmediateHttpResponse, NotFound
from tastypie.http import HttpAccepted, HttpBadRequest, HttpCreated
from tastypie.resources import Resource, ModelResource
from tastypie.utils import dict_strip_unicode_keys
from tastypie.utils.mime import determine_format, build_content_type
from tastypie.validation import FormValidation

from api.authentication import ConsumerApiKeyAuthentication, ConsumerAuthentication

# ===================================================
# = FIXME bastardized to no end Userena signup form =
# ===================================================
import random
from django.utils.hashcompat import sha_constructor
from userena.forms import SignupFormOnlyEmail
class SignupFormOnlyEmailBastardized(SignupFormOnlyEmail):
    def save(self):
        """ Generate a random username before falling back to parent signup form """
        while True:
            username = sha_constructor(str(random.random())).hexdigest()[:5]
            try:
                User.objects.get(username__iexact=username)
            except User.DoesNotExist: break

        self.cleaned_data['username'] = username

        username, email, password = (self.cleaned_data['username'],
                                     self.cleaned_data['email'],
                                     self.cleaned_data['password1'])

        new_user = User.objects.create_user(username, email, password)
        device_user_group = Group.objects.get(id=5)
        new_user.groups.add(device_user_group)
        return new_user

# ========
# = User =
# ========
class UserResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        list_allowed_methods = ('post',)
        detail_allowed_methods = ()
        authentication = ConsumerAuthentication()
        authorization = DjangoAuthorization()
        validation = FormValidation(form_class=SignupFormOnlyEmailBastardized)
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
        """Overriden to cancel persistence, since it's done in `is_valid`"""
        return bundle

    def post_list(self, request, **kwargs):
        """Overriden to inject ApiKey into response content"""
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
        deserialized = self.deserialize(request, request.raw_post_data, format=request.META.get('CONTENT_TYPE', 'application/json'))
        bundle = self.build_bundle(data=dict_strip_unicode_keys(deserialized))
        self.is_valid(bundle, request)
        post = request.POST.copy()
        post.update(bundle.data)
        request.POST = post
        request._dont_enforce_csrf_checks = True
        response = password_reset(request)
        return HttpCreated(location=response['location'])
