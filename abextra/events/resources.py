import os
import datetime

from django.core.urlresolvers import resolve, Resolver404, reverse
from django.core.paginator import Paginator, InvalidPage
from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib.sites.models import Site
from django.http import Http404
from sorl.thumbnail import get_thumbnail

from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.exceptions import ImmediateHttpResponse, NotFound
from tastypie.http import  HttpBadRequest
from tastypie.utils import trailing_slash

from api.authentication import ConsumerApiKeyAuthentication

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
        fields = ('title', 'color', 'button_icon', 'small_icon') +\
                 ('thumb',) # FIXME remove deprecated graphic fields

    def dehydrate_button_icon(self, bundle):
        category, data = bundle.obj, bundle.data
        if category.button_icon:
            return os.path.basename(category.button_icon.name)

    def dehydrate_small_icon(self, bundle):
        category, data = bundle.obj, bundle.data
        if category.small_icon:
            return os.path.basename(category.small_icon.name)

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

    def dehydrate_url(self, bundle):
        event, data = bundle.obj, bundle.data
        kwargs = dict(slug=event.slug, secret_key=event.secret_key)
        return '%(protocol)s://%(domain)s%(uri)s' % {
            'protocol': 'http',
            'domain': Site.objects.get_current().domain,
            'uri': reverse('event_detail', kwargs=kwargs),
            }

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
        try:
            image = event.image_chain(ctree)
            detail_thumb = get_thumbnail(image, **settings.IPHONE_THUMB_OPTIONS)
        except Exception:
            pass
        else:
            data.update(thumbnail_detail=detail_thumb.url)

        return super(EventResource, self).dehydrate(bundle)

    def get_object_list(self, request):
        """overridden to select relatives"""
        joined_qs = super(EventResource, self).get_object_list(request)\
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
        return super(OccurrenceResource, self).get_object_list(request)\
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

# =================
# = Event Summary =
# =================

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
        return super(EventSummaryResource, self).get_object_list(request)\
        .select_related('event', 'concrete_category', 'concrete_parent_category')

    def build_filters(self, filters=None):
        if filters is None:
            filters = dict()
        orm_filters = super(EventSummaryResource, self).build_filters(filters)

        # work with filter values that are Category resource uri(s)
        filter_uri = orm_filters.get('concrete_parent_category__exact')
        if filter_uri:
            try:
                view, args, kwargs = resolve(filter_uri)
            except Resolver404:
                raise NotFound("The URL provided '%s' was not a link to a valid resource." % filter_uri)
            else:
                orm_filters.update(concrete_parent_category__exact=kwargs['pk'])

        # FIXME these really need to be rethought and come from precomputed columns
        # FIXME inefficient joins for true occurrence-based results
        # TODO refactor to use regular tastypie field filtering
        # new and inefficient occurrence-wise price filter
        price_min, price_max = map(filters.get, ('price_min', 'price_max'))
        if price_min:
            price_min = int(price_min)
            orm_filters.update(event__occurrences__prices__quantity__gte=price_min)
        if price_max:
            price_max = int(price_max)
            orm_filters.update(event__occurrences__prices__quantity__lte=price_max)

        # new and inefficient occurrence-wise time filter
        time_range = map(filters.get, ('tstart_earliest', 'tstart_latest'))
        if all(time_range):
            mktime = lambda t: datetime.datetime.strptime(t, '%H%M').time()
            tstart_earliest, tstart_latest = map(mktime, time_range)
            orm_filters.update(event__occurrences__start_time__gte=tstart_earliest)
            orm_filters.update(event__occurrences__start_time__lte=tstart_latest)

        # new and inefficient occurrence-wise date filter
        date_range = map(filters.get, ('dtstart_earliest', 'dtstart_latest'))
        if all(date_range):
            mkdate = lambda d: datetime.datetime.strptime(d, '%Y-%m-%d').date()
            dtstart_earliest, dtstart_latest = map(mkdate, date_range)
            orm_filters.update(event__occurrences__start_date__gte=dtstart_earliest)
            orm_filters.update(event__occurrences__start_date__lte=dtstart_latest)

        # FIXME super hardcore inefficient -- full-text search should just live
        # on the summary itself
        ft_string = filters.get('q')
        if ft_string:
            events = Event.objects.only('id').ft_search(ft_string)
            orm_filters.update(event__in=events)

        return orm_filters

# =========================
# = Event Recommendations =
# =========================
class EventRecommendationResource(EventSummaryResource):
    def build_filters(self, request, filters=None):
        if filters is None:
            filters = dict()
        orm_filters = super(EventRecommendationResource, self).build_filters(filters)

        # pass-through of concrete_parent_category to summary
        cpc_filter = orm_filters.pop('concrete_parent_category__exact', None)
        if cpc_filter:
            orm_filters.update(summary__concrete_parent_category=cpc_filter)

        # TODO really ghetto removal of inherited occurrence-wise filters
        event_filters = tuple((k, v) for k, v in orm_filters.iteritems() if k.startswith('event__'))
        for k, v in event_filters:
            del orm_filters[k]
            orm_filters[k.split('__', 1)[1]] = v

        # declare Events queryset through active manager, with future filtering, orm_filters and action filters
        events_qs = Event.active.future().filter_user_actions(request.user, 'GX').filter(**orm_filters)

        # FIXME deprecated
        # should be deprecated as soon as proper filtering is in place
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
        # FIXME look into ml to make return consistent (either ids or objs)
        recommended_events = ml.recommend_events(request.user, events_qs)

        # FIXME ugly plug :: see above
        recommended_events = all(hasattr(e, 'pk') for e in recommended_events)\
                             and [e.pk for e in recommended_events] or recommended_events

        # preprocess ignores
        EventAction.objects.ignore_non_actioned_events(request.user, recommended_events)

        # orm filters are simple, when it comes down to it
        orm_filters = dict(event__in=recommended_events)
        return orm_filters

    def obj_get_list(self, request=None, **kwargs):
        """overridden just to pass the `request` as an arg to build_filters"""
        filters = request.GET.copy() if hasattr(request, 'GET') else dict()

        # Update with the provided kwargs.
        filters.update(kwargs)
        applicable_filters = self.build_filters(request, filters=filters)

        try:
            return self.get_object_list(request).filter(**applicable_filters)
        except ValueError:
            raise NotFound("Invalid resource lookup data provided (mismatched type).")
