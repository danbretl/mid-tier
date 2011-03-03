from collections import defaultdict

from piston.handler import BaseHandler
from piston.utils import rc, validate, require_mime, require_extended

from events.models import Event, Category, Occurrence
from events.utils import CachedCategoryTree

from behavior.models import EventAction

from learning import ml

from django.forms.models import model_to_dict

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

    def read(self, request):
        """
        Returns a single event if 'event_id' is given, otherwise a subset.
        """
        events_qs = Event.future.filter_user_actions(request.user, 'GX')
        ctree = CachedCategoryTree()

        try:
            category_id = int(request.GET.get('category_id'))
        except (ValueError, TypeError):
            recommended_events = ml.recommend_events(request.user, events_qs)
        else:
            all_children = ctree.children_recursive(ctree.get(id=category_id))
            events_qs = events_qs.filter(concrete_category__in=all_children)
            recommended_events = ml.recommend_events(request.user, events_qs)

        # FIXME a little unreliable and prolly outta place

        # FIXME optimization (should refactor with batch select?)
        occurrences = Occurrence.objects.select_related() \
            .filter(event__in=recommended_events)
        occurrences_by_event_id = defaultdict(lambda: [])
        for occurrence in occurrences:
            occurrence_dict = model_to_dict(occurrence, exclude=('event',))
            place_dict = model_to_dict(occurrence.place, exclude=('place_types',))
            occurrence_dict.update(place=place_dict)
            occurrences_by_event_id[occurrence.event_id].append(occurrence_dict)

        def to_dict(event):
            event_dict = model_to_dict(event, exclude=('categories', 'concrete_category', 'occurrences'))
            event_dict.update(occurrences=occurrences_by_event_id[event.id])
            event_dict.update(categories=[1,2,3])
            event_dict.update(concrete_category=ctree.surface_parent(
                ctree.get(id=event.concrete_category_id)
            ))
            return event_dict

        return [to_dict(event) for event in recommended_events]

class CategoryHandler(BaseHandler):
    allowed_methods = ('GET')
    model = Category
    fields = ('id', 'title', 'icon_path', 'color')

    def read(self, request, parent_node_slug='concrete'):
        """
        Returns immediate children of the parent category node
        """
        # FIXME shameless plug to fix nulled opt param - fix url handler
        if not parent_node_slug: parent_node_slug = 'concrete'
        ctree = CachedCategoryTree()
        return ctree.children(ctree.get(slug=parent_node_slug))

# Behavior

class EventActionHandler(BaseHandler):
    allowed_methods = ('GET', 'POST')
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

    # @validate(EventActionForm)
    # @require_extended
    def create(self, request):
        print 'tada'
        # import ipdb; ipdb.set_trace()
        return rc.CREATED
