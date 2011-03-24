from collections import defaultdict

from django.forms.models import model_to_dict
from piston.handler import BaseHandler
from piston.utils import rc, validate, require_mime, require_extended

from events.models import Event, Category, Occurrence, EventSummary
from events.utils import CachedCategoryTree
from behavior.models import EventAction
from prices.models import Price
from learning import ml
from api.utils import get_iphone_thumb

# Events

class EventHandler(BaseHandler):
    allowed_methods = ('GET')
    model = Event
    fields = (
        'id',
        'title',
        'description',
        'url',
        'image_url',
        'video_url',
        ('occurrences', (
            'id',
            'place',
            'one_off_place',
            'start_date',
            'start_time',
            'end_date',
            'end_time',
            'is_all_day',
            ('place', (
                'id',
                'title',
                'unit',
                'phone',
                'url',
                'image_url',
                'email',
                'description',
                'created',
                ('point', (
                    'id',
                    'latitude',
                    'longitude',
                    'address',
                    'zip',
                    'country',
                    ('city', (
                        'id',
                        'city',
                        'state')
                    )
                ))
            )),
            ('prices', (
                'quantity',
                'units',
                'remark',
            ))
        )),
        ('concrete_category', (
            'id',
            'title')
        ),
        ('categories', (
            'id',
            'title')
        ),
        ('place', (
            'title',
            'description',
            'url',
            'email',
            'phone',
            ('point', (
                'latitude',
                'longitute')
            )
        )),
    )

    def read(self, request, event_id=None):
        """
        Returns a single event if 'event_id' is given, otherwise a subset.
        """
        events_qs = Event.active.future().filter_user_actions(request.user, 'VI')
        ctree = CachedCategoryTree()

        try:
            category_id = int(request.GET.get('category_id'))
        except (ValueError, TypeError):
            if not event_id:
                recommended_events = ml.recommend_events(request.user, events_qs)
            else:
                #Debugging
                #return {'id':event_id}
                recommended_events = [Event.objects.get(id=event_id)]
        else:
            category = ctree.get(id=category_id)
            all_children = ctree.children_recursive(category)
            all_children.append(category)
            events_qs = events_qs.filter(concrete_category__in=all_children)
            recommended_events = ml.recommend_events(request.user, events_qs)

        # preprocess ignores
        if recommended_events:
            if len(recommended_events) > 1:
                non_actioned_events = Event.objects.raw(
                    """SELECT `events_event`.`id` FROM `events_event`
                    LEFT JOIN `behavior_eventaction`
                    ON (`events_event`.`id` = `behavior_eventaction`.`event_id` AND `behavior_eventaction`.`user_id` = %s)
                    WHERE (`events_event`.`id` IN %s) AND (`behavior_eventaction`.`id` IS NULL)
                    """, [request.user.id, [e.id for e in recommended_events]]
            )
            else:
                non_actioned_events = Event.objects.raw(
                    """SELECT `events_event`.`id` FROM `events_event`
                    LEFT JOIN `behavior_eventaction`
                    ON (`events_event`.`id` = `behavior_eventaction`.`event_id` AND `behavior_eventaction`.`user_id` = %s)
                    WHERE (`events_event`.`id` = %s) AND (`behavior_eventaction`.`id` IS NULL)
                    """, [request.user.id, recommended_events[0].id]
                    )
                
            if non_actioned_events:
                for event in non_actioned_events:
                    EventAction(event=event, user=request.user, action='I').save()

        # occurrence optimizations
        occurrences = Occurrence.objects.select_related('place__point__city') \
            .filter(event__in=recommended_events)

        # prices
        prices_by_occurrence_id = defaultdict(lambda: [])
        for price in Price.objects.filter(occurrence__in=occurrences):
            prices_by_occurrence_id[price.occurrence_id].append(price)

        occurrences_by_event_id = defaultdict(lambda: [])
        for occurrence in occurrences:
            occurrence_dict = model_to_dict(occurrence, exclude=('event',))
            place_dict = model_to_dict(occurrence.place, exclude=('place_types', 'image', 'image_url'))
            point_dict = model_to_dict(occurrence.place.point)
            point_dict.update(city=model_to_dict(occurrence.place.point.city, fields=('id', 'city', 'state')))
            place_dict.update(point=point_dict)
            occurrence_dict.update(place=place_dict)
            prices = prices_by_occurrence_id.get(occurrence.id)
            if prices: prices.sort(key=lambda p: p.quantity)
            occurrence_dict.update(
                prices=map(lambda p: model_to_dict(p, fields=('quantity', 'units', 'remark')), prices or [])
            )
            occurrences_by_event_id[occurrence.event_id].append(occurrence_dict)

        # abstract categories
        recommended_event_ids = map(lambda e: e.id, recommended_events)
        abstract_category_ids_by_event_id = Category.objects \
            .for_events(recommended_event_ids, 'A')

        category_to_dict = lambda c: model_to_dict(c, fields=('id',))

        def to_dict(event):
            event_dict = model_to_dict(event, exclude=('categories', 'concrete_category', 'occurrences', 'slug', 'submitted_by', 'xid', 'image', 'image_url'))

            # occurrences
            event_dict.update(occurrences=occurrences_by_event_id[event.id])

            # concrete category
            concrete_category = ctree.get(id=event.concrete_category_id)
            event_dict.update(concrete_category_id=concrete_category.id)

            # concrete parent
            concrete_parent_category = ctree.surface_parent(concrete_category)
            event_dict.update(concrete_parent_category_id=concrete_parent_category.id)

            # concrete breadcrumbs :)
            concrete_breadcrumbs = ctree.parents(concrete_category)
            event_dict.update(concrete_breadcrumb_ids=[c.id for c in concrete_breadcrumbs])

            # abstract categories
            abstract_category_ids = abstract_category_ids_by_event_id[event.id]
            abstract_categories = [
                model_to_dict(ctree.get(id=c_id), fields=('id',)) \
                    for c_id in abstract_category_ids
            ]
            event_dict.update(categories=abstract_categories)

            # image url
            image = event.image_chain(ctree)
            thumb = get_iphone_thumb(image)
            event_dict.update(image_url=thumb.url)

            return event_dict

        return [to_dict(event) for event in recommended_events]

class CategoryHandler(BaseHandler):
    allowed_methods = ('GET')
    model = Category
    fields = ('id', 'title', 'color')

    def read(self, request):
        return Category.concrete.all()

class EventListDetailHandler(BaseHandler):
    """
    """
    allowed_methods = ('GET')
    model = EventSummary
    fields = ('id', 'title', 'description', 'url', 'concrete_category',
              'date_range', 'price_range', 'time', 'place')
    
    def read(self, request):
        """
        Returns a single event if 'event_id' is given, otherwise a subset.
        """
        events_qs = Event.active.future().filter_user_actions(request.user, 'VI')
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
        if recommended_events:
            non_actioned_events = Event.objects.raw(
                """SELECT `events_event`.`id` FROM `events_event`
                    LEFT JOIN `behavior_eventaction`
                    ON (`events_event`.`id` = `behavior_eventaction`.`event_id` AND `behavior_eventaction`.`user_id` = %s)
                    WHERE (`events_event`.`id` IN %s) AND (`behavior_eventaction`.`id` IS NULL)
                """, [request.user.id, [e.id for e in recommended_events]]
            )
            if non_actioned_events:
                for event in non_actioned_events:
                    EventAction(event=event, user=request.user, action='I').save()
        recommended_event_ids = [event.id for event in recommended_events]

        return EventSummary.objects.filter(id__in=recommended_event_ids)

# Behavior

class EventActionHandler(BaseHandler):
    allowed_methods = ('GET')
    model = EventAction
    fields = ('action',
        ('user', ('id',)),
        ('event', ('id',)),
    )

    def read(self, request, event_id=None):
        """Returns a single event action if 'event_id' is given"""
        user = request.user
        try:
            response = EventAction.objects.get(user=user, event=event_id)
        except EventAction.DoesNotExist:
            response = rc.NOT_FOUND
            response.write(u'No user action exists for event [%s].' % event_id)
        return response
