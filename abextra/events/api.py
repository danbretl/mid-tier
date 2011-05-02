from tastypie import fields
from tastypie.resources import ModelResource
from events.models import Event, Occurrence, Category, EventSummary
from tastypie.authentication import BasicAuthentication, ApiKeyAuthentication
from tastypie.authorization import DjangoAuthorization

from tastypie.constants import ALL, ALL_WITH_RELATIONS
from newapi.authentication import ConsumerApiKeyAuthentication, ConsumerAuthentication

from places.api import PlaceResource, PlaceFullResource

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
        detail_allowed_methods = ()
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

# ============
# = Category =
# ============
class CategoryResource(ModelResource):
    class Meta:
        queryset = Category.concrete.all()
        allowed_methods = ('get',)
        authentication = ConsumerApiKeyAuthentication()
        limit = 200
        fields = ('title', 'color')

# ==============
# = Occurrence =
# ==============
class OccurrenceResource(ModelResource):
    place = fields.ToOneField(PlaceResource, 'place')

    class Meta:
        queryset = Occurrence.objects.all()
        allowed_methods = ('get',)
        authentication = ConsumerApiKeyAuthentication()
        excludes = ('id',)

    def get_object_list(self, request):
        """overridden to select relatives"""
        return super(OccurrenceResource, self).get_object_list(request) \
            .select_related('place__point__city')

class OccurrenceFullResource(OccurrenceResource):
    place = fields.ToOneField(PlaceFullResource, 'place', full=True)

    class Meta(OccurrenceResource.Meta):
        resource_name = 'occurrence_full'

# =========
# = Event =
# =========
from events.utils import CachedCategoryTree
from sorl.thumbnail import get_thumbnail
from django.conf import settings

class EventResource(ModelResource):
    concrete_category = fields.ToOneField(CategoryResource, 'concrete_category')
    abstract_categories = fields.ToManyField(CategoryResource, 'categories')
    occurrences = fields.ToManyField(OccurrenceResource, 'occurrences')

    class Meta:
        queryset = Event.objects.all()
        allowed_methods = ('get',)
        authentication = ConsumerApiKeyAuthentication()
        fields = ('concrete_category', 'abstract_categories', 'occurrences',
            'title', 'description', 'image', 'video_url', 'url'
        )

    def dehydrate(self, bundle):
        """inject extra info"""
        event, data = bundle.obj, bundle.data
        category_resource = self.concrete_category.get_related_resource(
            bundle.obj.concrete_category
        )
        ctree = CachedCategoryTree()

        # concrete parent category
        concrete_parent_category = ctree.surface_parent(event.concrete_category_id)
        concrete_parent_category_uri = category_resource.get_resource_uri(concrete_parent_category)
        data.update(concrete_parent_category=concrete_parent_category_uri)

        # concrete breadcrumbs :)
        concrete_category_breadcrumb_uris = []
        for category in ctree.parents(event.concrete_category_id):
            concrete_category_breadcrumb_uris.append(
                category_resource.get_resource_uri(category)
            )
        data.update(concrete_category_breadcrumbs=concrete_category_breadcrumb_uris)

        # detail image thumbnail
        image = event.image_chain(ctree)
        detail_thumb = get_thumbnail(image, **settings.IPHONE_THUMB_OPTIONS)
        data.update(detail_thumbnail=detail_thumb.url)

        return super(EventResource, self).dehydrate(bundle)

    def get_object_list(self, request):
        """overridden to select relatives"""
        return super(EventResource, self).get_object_list(request) \
            .select_related('concrete_category',)


class EventFullResource(EventResource):
    occurrences = fields.ToManyField(OccurrenceFullResource, 'occurrences', full=True)

    class Meta(EventResource.Meta):
        resource_name = 'event_full'

# =================
# = Event Summary =
# =================
class EventSummaryResource(ModelResource):
    event = fields.ToOneField(EventResource, 'event')
    concrete_category = fields.ToOneField(CategoryResource, 'concrete_category')
    concrete_parent_category = fields.ToOneField(CategoryResource, 'concrete_parent_category')

    class Meta:
        queryset = EventSummary.objects.all()
        allowed_methods = ('get',)
        authentication = ConsumerApiKeyAuthentication()
        filtering = {
            'concrete_category': ('exact',),
            'concrete_parent_category': ('exact',)
        }

    def get_object_list(self, request):
        """overridden to select relatives"""
        return super(EventSummaryResource, self).get_object_list(request) \
            .select_related('event', 'concrete_category', 'concrete_parent_category')


# =========================
# = Event Recommendations =
# =========================
from behavior.models import EventAction
from learning import ml

class EventRecommendationResource(EventSummaryResource):

    def build_filters(self, request, filters=None):
        if filters is None:
            filters = {}
        orm_filters = super(EventSummaryResource, self).build_filters(filters)

        if orm_filters.has_key('concrete_parent_category__exact'):
            filter_value = orm_filters['concrete_parent_category__exact']
            orm_filters.update(summary__concrete_parent_category=filter_value)
            del orm_filters['concrete_parent_category__exact']

        # filter initial event queryset
        events_qs = Event.active.future().filter(**orm_filters) \
            .filter_user_actions(request.user, 'VI')

        # use machine learning
        recommended_events = ml.recommend_events(request.user, events_qs)

        # preprocess ignores
        EventAction.objects.ignore_non_actioned_events(request.user, recommended_events)

        return dict(event__in=recommended_events)

    def obj_get_list(self, request=None, **kwargs):
        """overriden just to pass the `request` as an arg to `build_filters`"""
        filters = {}

        if hasattr(request, 'GET'):
            # Grab a mutable copy.
            filters = request.GET.copy()

        # Update with the provided kwargs.
        filters.update(kwargs)
        applicable_filters = self.build_filters(request, filters=filters)

        try:
            return self.get_object_list(request).filter(**applicable_filters)
        except ValueError, e:
            raise NotFound("Invalid resource lookup data provided (mismatched type).")
