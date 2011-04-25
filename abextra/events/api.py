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

class UserResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        allowed_methods = ('post',)
        authentication = ConsumerAuthentication()
        authorization = DjangoAuthorization()
        validation = FormValidation(form_class=UserCreationForm)

    def hydrate_password(self, bundle):
        user = bundle.obj
        raw_password = bundle.data['password1']
        user.set_password(raw_password)
        return bundle

# ============
# = Category =
# ============
class CategoryResource(ModelResource):
    parent = fields.ToOneField('self', 'parent')
    class Meta:
        queryset = Category.objects.all()
        allowed_methods = ('get',)

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
