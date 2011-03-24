from django.db.models.query import CollectedObjects
from django.db import models
from events.models import Event, Occurrence, EventSummary
from prices.models import Price


def summarize_event(event, commit=False):
    e_s = EventSummary()
    # This is interesting: http://djangosnippets.org/snippets/1258/
    #related_objs = CollectedObjects()
    #event._collect_sub_objects(related_objs)
    #Event.objects.select_related()
    e_s.id = event.id
    e_s.concrete_category = event.concrete_category.title
    occurrence_objs = event.occurrences.all()
    dates = [o_obj.start_date for o_obj in occurrence_objs]
    date_range = [min(dates),max(dates)]
    e_s.date_range = ' - '.join([dt.strftime('%x') for dt in date_range])
    e_s.title = event.title
    e_s.url = event.url
    e_s.description = event.description
    
    occ_obj = None
    try:
        time, occ_obj = min([(o_obj.start_time, o_obj)
                             for o_obj in occurrence_objs if o_obj.start_time])
    except:
        e_s.time = 'N/A'
        occ_obj = occurrence_objs[0]
    
    e_s.place = occ_obj.place.full_title + ',' + occ_obj.place.address
    price_objs = [price.quantity for price in occ_obj.prices.all()]
    e_s.price_range = str(min(price_objs)) + ' - ' + str(max(price_objs))
    if commit:
             e_s.save()
    return e_s

def summarize_events(events):
    event_objs = Event.objects.filter(id__in=events)
    lst = []
    for event in event_objs:
        lst.append(summarize_event(event, True))

    return lst

# This will be the general form of the event_summarizer and should be able
# to summarize any django object into a summary list. 
# class Summarizer(models.Model):

 
