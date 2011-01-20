from piston.handler import BaseHandler
from piston.utils import rc, require_mime, require_extended
from events.models import Event
from behavior.models import EventAction

class EventHandler(BaseHandler):
    allowed_methods = ('GET', 'POST')
    model = Event
    fields = (
        'title',
        'description',
        'url',
        'image_url',
        'video_url',
        'one_off_place',
        ('event_times', (
            'id',
            'start',
            'end')
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
                'longitute'
            ))
        )),
    )

    def read(self, request, event_id=None):
        """
        Returns a single event if 'event_id' is given,
        otherwise a subset.
        """
        m = Event.objects
        return m.filter(pk=event_id) if event_id else m.all()[:20]

    # def create(self, request):
    #     """Creates a new EventAction."""
    #     attrs = self.flatten_dict(request.POST)
    # 
    #     if self.exists(**attrs):
    #     return rc.DUPLICATE_ENTRY
    #     else:
    #     post = Blogpost(title=attrs['title'], 
    #                     content=attrs['content'],
    #                     author=request.user)
    #     post.save()
    # 
    #     return post

class EventActionHandler(BaseHandler):
    allowed_methods = ('POST')
    model = EventAction

    def read(self, request, event_id=None):
        """docstring for read"""
        pass