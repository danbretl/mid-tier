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

# =========
# = Event =
# =========
class EventResource(ModelResource):
    concrete_category = fields.ToOneField(CategoryResource, 'concrete_category')

    class Meta:
        queryset = Event.objects.all()
        allowed_methods = ('get',)
        authentication = ConsumerApiKeyAuthentication()

class EventSummaryResource(ModelResource):
    event = fields.ToOneField(EventResource, 'event')
    concrete_category = fields.ToOneField(CategoryResource, 'concrete_category')

    class Meta:
        queryset = EventSummary.objects.all()
        allowed_methods = ('get',)
        authentication = ConsumerApiKeyAuthentication()

# =========================
# = Event Recommendations =
# =========================
from events.utils import CachedCategoryTree
from behavior.models import EventAction
from learning import ml

class EventRecommendationResource(EventSummaryResource):

    def build_filters(self, request, filters=None):
        if filters is None:
            filters = {}

        orm_filters = super(EventSummaryResource, self).build_filters(filters)

        events_qs = Event.active.future()
        # if search_terms:
        #     events_qs = events_qs.filter(title__search=search_terms)
        # else:
        events_qs = events_qs.filter_user_actions(request.user, 'VI')

        ctree = CachedCategoryTree()
        try:
            category_id = int(request.GET.get('category_id'))
        except (ValueError, TypeError):
            recommended_events = ml.recommend_events(request.user, events_qs)
        else:
            category = ctree.get(id=category_id)
            all_children = ctree.children_recursive(category)
            all_children.append(category)
            events_qs = events_qs.filter(concrete_category__in=all_children)
            recommended_events = ml.recommend_events(request.user, events_qs)

        # preprocess ignores
        recommended_event_ids = [event.id for event in recommended_events]
        if recommended_event_ids:
            ids_param = recommended_event_ids \
                if len(recommended_event_ids) > 1 else recommended_event_ids[0]
            non_actioned_events = Event.objects.raw(
                """SELECT `events_event`.`id` FROM `events_event`
                LEFT JOIN `behavior_eventaction`
                ON (`events_event`.`id` = `behavior_eventaction`.`event_id` AND `behavior_eventaction`.`user_id` = %s)
                WHERE (`events_event`.`id` IN %s) AND (`behavior_eventaction`.`id` IS NULL)
                """, [request.user.id, ids_param]
            )
            if non_actioned_events:
                for event in non_actioned_events:
                    EventAction(event=event, user=request.user, action='I').save()

        orm_filters = dict(event__in=recommended_event_ids)
        return orm_filters

    def obj_get_list(self, request=None, **kwargs):
        """
        A ORM-specific implementation of ``obj_get_list``.

        Takes an optional ``request`` object, whose ``GET`` dictionary can be
        used to narrow the query.
        """
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
