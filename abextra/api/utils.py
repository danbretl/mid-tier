from django.conf import settings
from django.forms.models import model_to_dict
from sorl.thumbnail import get_thumbnail

from events.models import Category, Occurrence
from prices.models import Price

def get_iphone_thumb(my_file):
    return get_thumbnail(my_file, **settings.IPHONE_THUMB_OPTIONS)

#FIXME ugly piece of code - make part of EventManager?
def event_dict(events, ctree):
    # occurrence optimizations
    occurrences = Occurrence.objects.select_related('place__point__city') \
        .filter(event__in=events)

    # prices
    prices_by_occurrence_id = {}
    for price in Price.objects.filter(occurrence__in=occurrences):
        prices_by_occurrence_id.setdefault(price.occurrence_id, []).append(price)

    occurrences_by_event_id = {}
    for occurrence in occurrences:
        occurrence_dict = model_to_dict(occurrence, exclude=('event',))
        place_dict = model_to_dict(occurrence.place, exclude=('place_types', 'image', 'image_url'))
        point_dict = model_to_dict(occurrence.place.point)
        point_dict.update(city=model_to_dict(occurrence.place.point.city, fields=('id', 'city', 'state')))
        place_dict.update(point=point_dict)
        occurrence_dict.update(place=place_dict)
        prices = prices_by_occurrence_id.get(occurrence.id) or []
        prices.sort(key=lambda p: p.quantity)
        occurrence_dict.update(
            prices=map(lambda p: model_to_dict(p, fields=('quantity', 'units', 'remark')), prices)
        )
        occurrences_by_event_id.setdefault(occurrence.event_id, []).append(occurrence_dict)

    # abstract categories
    event_ids = map(lambda e: e.id, events)
    abstract_category_ids_by_event_id = Category.objects \
        .for_events(event_ids, 'A')

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
        abstract_categories = abstract_category_ids
        event_dict.update(categories=abstract_categories)

        # image url
        image = event.image_chain(ctree)
        thumb = get_iphone_thumb(image)
        event_dict.update(image_url=thumb.url)

        return event_dict

    return map(to_dict, events)