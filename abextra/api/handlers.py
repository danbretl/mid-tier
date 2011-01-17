from piston.handler import BaseHandler
from events.models import Event

class EventHandler(BaseHandler):
   allowed_methods = ('GET',)
   model = Event

   def read(self, request, event_id=None):
        """
        Returns a single event if 'event_id' is given,
        otherwise a subset.
        """
        m = Event.objects
        return m.filter(pk=event_id) if event_id else m.all()