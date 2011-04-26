from tastypie import fields
from tastypie.resources import ModelResource
from events.models import Event, Category, EventSummary
from tastypie.authentication import BasicAuthentication, ApiKeyAuthentication
from tastypie.authorization import DjangoAuthorization

from tastypie.constants import ALL, ALL_WITH_RELATIONS
from newapi.authentication import ConsumerApiKeyAuthentication, ConsumerAuthentication

# ========
# = User =
# ========
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from tastypie.validation import FormValidation
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.http import HttpAccepted, HttpBadRequest
from tastypie.utils.mime import determine_format, build_content_type

class UserResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        allowed_methods = ('post',)
        detail_allowed_methods = []
        authentication = ConsumerAuthentication()
        authorization = DjangoAuthorization()
        validation = FormValidation(form_class=UserCreationForm)

    def hydrate_password(self, bundle):
        user = bundle.obj
        raw_password = bundle.data['password1']
        user.set_password(raw_password)
        return bundle

    def post_list(self, request, **kwargs):
        response = super(UserResource, self).post_list(request, **kwargs)
        import ipdb; ipdb.set_trace()
        return response

    # def is_valid(self, bundle, request=None):
    #     username = bundle.data.get('username')
    #     if username:
    #         try:
    #             existing_user = User.objects.get(username=username)
    #         except (User.DoesNotExist, User.MultipleObjectsReturned):
    #             pass
    #         else:
    #             data = dict(api_key=existing_user.api_key.key)
    #             desired_format = self.determine_format(request) if request \
    #                 else self._meta.default_format
    #             serialized = self.serialize(request, data, desired_format)
    #             response = HttpBadRequest(
    #                 content=serialized,
    #                 content_type=build_content_type(desired_format)
    #             )
    #             # import ipdb; ipdb.set_trace()
    #             raise ImmediateHttpResponse(response=response)
    #     super(UserResource, self).is_valid(bundle, request)

class AnonymousUserResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        allowed_methods = ('post',)
        detail_allowed_methods = []
        authentication = ConsumerAuthentication()
        authorization = DjangoAuthorization()
        validation = FormValidation(form_class=UserCreationForm)

    def hydrate_username(self, bundle):
        bundle.obj.username = bundle.data['udid']
        return bundle

    def hydrate_password(self, bundle):
        raw_password = User.objects.make_random_password()
        bundle.obj.set_password(raw_password)
        return bundle

# ============
# = Category =
# ============
class CategoryResource(ModelResource):
    class Meta:
        queryset = Category.concrete.all()
        allowed_methods = ('get',)
        authentication = ConsumerApiKeyAuthentication()

# =========
# = Event =
# =========
class EventResource(ModelResource):
    concrete_category = fields.ToOneField(CategoryResource, 'concrete_category')

    class Meta:
        queryset = Event.objects.all()
        allowed_methods = ('get', 'post')
        authentication = ConsumerAuthentication()
        filtering = {"title": ALL}

    def build_filters(self, filters=None):
        if filters is None:
            filters = {}

        orm_filters = super(EventResource, self).build_filters(filters)
        orm_filters = {"pk__in": range(10)}
        return orm_filters

class EventSummaryResource(ModelResource):
    class Meta:
        queryset = EventSummary.objects.all()
        allowed_methods = ('get',)

    def build_filters(self, filters=None):
        if filters is None:
            filters = {}

        orm_filters = super(EventSummaryResource, self).build_filters(filters)
        # import ipdb; ipdb.set_trace()
        orm_filters = {"pk__in": range(10)}

        return orm_filters
