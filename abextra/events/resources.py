from django.core.urlresolvers import resolve, Resolver404
from django.conf import settings
from sorl.thumbnail import get_thumbnail

from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.authentication import ApiKeyAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.validation import FormValidation
from tastypie.exceptions import ImmediateHttpResponse, NotFound
from tastypie.http import HttpAccepted, HttpBadRequest
from tastypie.utils.mime import determine_format, build_content_type
from tastypie.constants import ALL, ALL_WITH_RELATIONS

from api.authentication import ConsumerApiKeyAuthentication, ConsumerAuthentication

from places.resources import PlaceResource, PlaceFullResource
from prices.resources import PriceResource

from events.models import Event, Occurrence, Category, EventSummary
from events.utils import CachedCategoryTree

from behavior.models import EventAction
from learning import ml

# ============
# = Category =
# ============
class CategoryResource(ModelResource):
    class Meta:
        queryset = Category.concrete.all()
        list_allowed_methods = ('get',)
        detail_allowed_methods = ()
        authentication = ConsumerApiKeyAuthentication()
        limit = 200
        fields = ('title', 'color', 'button_icon', 'small_icon') + \
            ('thumb',) # FIXME remove deprecated graphic fields

    def dehydrate_button_icon(self, bundle):
        category, data = bundle.obj, bundle.data
        return category.button_icon.url if category.button_icon else None

    def dehydrate_small_icon(self, bundle):
        category, data = bundle.obj, bundle.data
        return category.small_icon.url if category.small_icon else None

    # FIXME remove deprecated
    def dehydrate_thumb(self, bundle):
        category, data = bundle.obj, bundle.data
        return category.thumb_path

# =========
# = Event =
# =========
class EventResource(ModelResource):
    concrete_category = fields.ToOneField(CategoryResource, 'concrete_category')
    abstract_categories = fields.ToManyField(CategoryResource, 'categories')
    occurrences = fields.ToManyField('events.resources.OccurrenceResource', 'occurrences')

    class Meta:
        queryset = Event.objects.all()
        list_allowed_methods = ()
        detail_allowed_methods = ('get',)
        authentication = ConsumerApiKeyAuthentication()
        fields = ('concrete_category', 'abstract_categories', 'occurrences',
            'title', 'description', 'image', 'video_url', 'url'
        )

    # TODO refactor into separate fields / hydration methods when ctree becomes thread-local
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
        data.update(thumbnail_detail=detail_thumb.url)

        return super(EventResource, self).dehydrate(bundle)

    def get_object_list(self, request):
        """overridden to select relatives"""
        joined_qs = super(EventResource, self).get_object_list(request) \
            .select_related('concrete_category')
        return joined_qs


class EventFullResource(EventResource):
    occurrences = fields.ToManyField('events.resources.OccurrenceFullResource', 'occurrences', full=True)

    class Meta(EventResource.Meta):
        resource_name = 'event_full'


class FeaturedEventResource(EventFullResource):
    class Meta(EventFullResource.Meta):
        queryset = Event.objects.featured()
        list_allowed_methods = ('get',)
        detail_allowed_methods = ()
        resource_name = 'event_featured'


# ==============
# = Occurrence =
# ==============
class OccurrenceResource(ModelResource):
    event = fields.ToOneField(EventResource, 'event')
    place = fields.ToOneField(PlaceResource, 'place')
    prices = fields.ToManyField(PriceResource, 'prices')

    class Meta:
        queryset = Occurrence.objects.future()
        list_allowed_methods = ('get',)
        detail_allowed_methods = ('get',)
        authentication = ConsumerApiKeyAuthentication()
        excludes = ('id',)

    def get_object_list(self, request):
        """overridden to select relatives"""
        return super(OccurrenceResource, self).get_object_list(request) \
            .select_related('place__point__city')

    def build_filters(self, filters=None):
        """Allows flexible lookup by either PK or URI"""
        if filters is None:
            filters = {}

        orm_filters = super(OccurrenceResource, self).build_filters(filters)

        event_filter = orm_filters.get('event__exact')
        if event_filter and event_filter.startswith('/'):
            try:
                view, args, kwargs = resolve(event_filter)
            except Resolver404:
                raise NotFound("The URL provided '%s' was not a link to a valid resource." % event_filter)
            else:
                orm_filters.update(event__exact=kwargs.get('pk'))

        return orm_filters

class OccurrenceFullResource(OccurrenceResource):
    place = fields.ToOneField(PlaceFullResource, 'place', full=True)
    prices = fields.ToManyField(PriceResource, 'prices', full=True)

    class Meta(OccurrenceResource.Meta):
        resource_name = 'occurrence_full'
        filtering = {'event': ('exact',)}

# =========================================
# = Event Summary including Haystack search
# =========================================
from haystack.query import SearchQuerySet

class EventSummaryResource(ModelResource):
    event = fields.ToOneField(EventFullResource, 'event')
    concrete_category = fields.ToOneField(CategoryResource, 'concrete_category')
    concrete_parent_category = fields.ToOneField(CategoryResource, 'concrete_parent_category')

    class Meta:
        queryset = EventSummary.objects.all()
        list_allowed_methods = ('get',)
        detail_allowed_methods = ()
        authentication = ConsumerApiKeyAuthentication()
        filtering = {
            'concrete_category': ('exact',),
            'concrete_parent_category': ('exact',)
        }

    def get_object_list(self, request):
        """overridden to select relatives"""
        return super(EventSummaryResource, self).get_object_list(request) \
            .select_related('event', 'concrete_category', 'concrete_parent_category')

    def build_filters(self, filters=None):
        if filters is None:
            filters = dict()
        orm_filters = super(EventSummaryResource, self).build_filters(filters)

        filter_uri = orm_filters.get('concrete_parent_category__exact')
        if filter_uri:
            try:
                view, args, kwargs = resolve(filter_uri)
            except Resolver404:
                raise NotFound("The URL provided '%s' was not a link to a valid resource." % filter_uri)
            else:
                orm_filters.update(concrete_parent_category__exact=kwargs['pk'])

        if 'q' in filters:
            sqs = SearchQuerySet().auto_query(filters['q'])

            orm_filters["pk__in"] = [ i.pk for i in sqs ]

        return orm_filters

# =========================
# = Event Recommendations =
# =========================
class EventRecommendationResource(EventSummaryResource):

    def build_filters(self, request, filters=None):
        if filters is None:
            filters = dict()
        orm_filters = super(EventRecommendationResource, self).build_filters(filters)

        # passthrough of concrete_parent_category to summary
        cpc_filter = orm_filters.pop('concrete_parent_category__exact', None)
        if cpc_filter:
            orm_filters.update(summary__concrete_parent_category=cpc_filter)

        events_qs = Event.active.future().filter(**orm_filters).filter_user_actions(request.user, 'GX')
        view = filters.get('view')
        if view:
            if view == 'popular':
                events_qs = events_qs.order_by('-popularity_score')[:100]
            elif view == 'free':
                ids = EventSummary.objects.filter(price_quantity_max=0).values_list('event',
                                                                     flat=True)
                events_qs = events_qs.filter(id__in=ids)[:100]
            else:
                msg = "Invalid value for get parameter 'view'"
                response = HttpBadRequest(content=msg)
                raise ImmediateHttpResponse(response=response)

        # use machine learning
        recommended_events = ml.recommend_events(request.user, events_qs)

        # preprocess ignores
        EventAction.objects.ignore_non_actioned_events(request.user, recommended_events)

        # orm filters are simple, when it comes down to it
        orm_filters = dict(event__in=recommended_events)

        return orm_filters

    def obj_get_list(self, request=None, **kwargs):
        """overriden just to pass the `request` as an arg to `build_filters`"""
        filters = request.GET.copy() if hasattr(request, 'GET') else dict()

        # Update with the provided kwargs.
        filters.update(kwargs)
        applicable_filters = self.build_filters(request, filters=filters)

        try:
            return self.get_object_list(request).filter(**applicable_filters)
        except ValueError, e:
            raise NotFound("Invalid resource lookup data provided (mismatched type).")
