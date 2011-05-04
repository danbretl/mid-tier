from django.core.urlresolvers import resolve, Resolver404
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings
from sorl.thumbnail import get_thumbnail

from tastypie import fields
from tastypie.authentication import Authentication
from tastypie.authorization import DjangoAuthorization, Authorization
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.exceptions import ImmediateHttpResponse, NotFound
from tastypie.http import HttpAccepted, HttpBadRequest
from tastypie.resources import ModelResource
from tastypie.utils.mime import determine_format, build_content_type
from tastypie.validation import FormValidation

from api.authentication import ConsumerApiKeyAuthentication, ConsumerAuthentication
# from api.models import DeviceUdid # FIXME generic tool - find a better place

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
        return new_user

# ========
# = User =
# ========
class UserResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        allowed_methods = ('post',)
        detail_allowed_methods = ()
        authentication = ConsumerAuthentication()
        authorization = Authorization()
        validation = FormValidation(form_class=SignupFormOnlyEmailBastardized)

    def is_valid(self, bundle, request=None):
        # username = DeviceUdid.objects.generate_username_unique(prefix='')
        # bundle.data.update(username=username)
        form = self._meta.validation.form_class(data=bundle.data)

        # validation
        if form.is_valid():
            form.save()

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
        return bundle
