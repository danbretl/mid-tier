"""
Author: Vikas Menon
Created: Mar 24, 2011
"""

from events.models import Event, EventSummary
from events.utils import CachedCategoryTree



def summarize_events(events):
    """
    Argument:
     'events' : A list of event ids
    This is a wrapper to summarize_event and gets called for
    all ids passed in events 
    """
    event_objs = Event.objects.filter(id__in=events)
    lst = []
    ctree = CachedCategoryTree()
    for event in event_objs:
        lst.append(summarize_event(event, ctree, True))

    return lst


 
