"""
Author: Vikas Menon
Created: Mar 24, 2011
"""

from events.models import Event, EventSummary
from events.utils import CachedCategoryTree

def summarize_event(event, ctree, commit=False):
    """
    Arguments:
     'event' : A django event object.
     'commit': A flag that saves the event summary if set. Mostly for debugging.
    Summarize a single event for the UI.
    Why: Performance. This ensure when a user makes a request, we don't need
    to perform any joins and can return information from a single table.
    When: This is performed after a scrape and before the information gets
    stored on the event database.
    """
    if not event:
        return
    if not ctree:
        ctree = CachedCategoryTree()
    
    e_s = EventSummary()
    # This is interesting: http://djangosnippets.org/snippets/1258/
    #related_objs = CollectedObjects()
    #event._collect_sub_objects(related_objs)
    #Event.objects.select_related()
    e_s.id = event
    e_s.concrete_category = ctree.surface_parent(event.concrete_category)
    e_s.title = event.title
    e_s.url = event.url
    e_s.description = event.description

    # ToDo: We could potentially filter out any events here that do not have
    # future occurrences. Since we are using this for scrape, the
    # expectations is that past events don't get scraped. 

    #Get occurrence related information. 
    occurrence_objs = event.occurrences.all()
    # If there are no occurrence objects, then the event hasn't been
    # scheduled for a date, time and place. Forget this event. 
    if not occurrence_objs:
        return
    dates = [o_obj.start_date for o_obj in occurrence_objs]
    date_range = [min(dates), max(dates)]
    e_s.date_range = ' - '.join([dt.strftime('%x') for dt in date_range])
    occ_obj = None 

    try:
        # min could potentially be run on an empty list (since invalid times get
        # filtered out)
        time, occ_obj = min([(o_obj.start_time, o_obj)
                             for o_obj in occurrence_objs if o_obj.start_time])
        e_s.time = time.strftime('%X')
    except:
        e_s.time = 'N/A'
        occ_obj = occurrence_objs[0]
        
    try:
        e_s.place = occ_obj.place.full_title + ',' + occ_obj.place.address
    except:
        # This also imples a bad scrape. We have an occurrence
        # without a place/location.
        e_s.place = 'Unavailable'

    price_objs = [price.quantity for price in occ_obj.prices.all()]
    try:
        #min could potentially be run on an empty list of price objs. 
        e_s.price_range = str(min(price_objs)) + ' - ' + str(max(price_objs))
    except:
        e_s.price_range = 'N/A'
        
    if commit:
        # Here we can also check if the event_summary already exists and
        # update relevant information accordingly. 
        e_s.save()
    return e_s

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


 
