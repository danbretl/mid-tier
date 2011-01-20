from piston.handler import BaseHandler
from piston.utils import rc, validate, require_mime, require_extended

#########
# Event #
#########
from events.models import Event

class EventHandler(BaseHandler):
    allowed_methods = ('GET', 'POST')
    model = Event
    fields = ('title', 'description', 'url', 'image_url', 'video_url', 'one_off_place',
        ('event_times', ('id', 'start', 'end')),
        ('categories', ('id', 'title')),
        ('place', ('title', 'description', 'url', 'email', 'phone', ('point', ('latitude','longitute')))),
    )

    def read(self, request, event_id=None):
        """
        Returns a single event if 'event_id' is given,
        otherwise a subset.
        """
        m = Event.objects
        return m.filter(pk=event_id) if event_id else m.all()[:20]

###############
# EventAction #
###############
from django import forms
from behavior.models import EventAction

class EventActionForm(forms.ModelForm):
    class Meta:
        model = EventAction

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
    def create(self, request):
        print 'tada'
        import ipdb; ipdb.set_trace()
        return rc.CREATED
