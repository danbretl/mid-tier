from piston.handler import BaseHandler
from piston.utils import rc, validate, require_mime, require_extended

from events.models import Event, Category
from events.utils import CachedCategoryTree

from behavior.models import EventAction

from learning import ml

# Events

class EventHandler(BaseHandler):
    allowed_methods = ('GET', 'POST')
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

    def read(self, request, event_id=None):
        """
        Returns a single event if 'event_id' is given,
        otherwise a subset.
        """
        m = Event.objects

        # FIXME this should not live here
        recommended_categories = ml.recommend_categories(request.user)

        # FIXME brute force
        events = set()

        for category in recommended_categories:
            event = Category.objects.get(id=category).events_concrete.order_by('?')[0]
            events.add(event)

        # TODO make sure to not send Xed events - check event actions
        # FIXME make more efficient
        actions_x = EventAction.objects.filter(user=request.user, event__in=events, action='X')
        removed_events = set((a.event for a in actions_x))

        return m.filter(pk=event_id) if event_id else list(events - removed_events)
        # return m.filter(pk=event_id) if event_id else m.all()[:20]

class CategoryHandler(BaseHandler):
    allowed_methods = ('GET')
    model = Category
    fields = ('id', 'title', 'icon_path')

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
