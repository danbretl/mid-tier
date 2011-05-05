from haystack import indexes
from haystack import site
from events.models import Event

class EventIndex(indexes.SearchIndex):
    text = indexes.CharField(document=True, use_template=True)
    # Regarding boosting: http://readthedocs.org/docs/django-haystack/v1.1/boost.html#field-boost.
    # FIXME: This however does not work with the current version.
    title = indexes.CharField(model_attr='title')#, boost=1.5)
    description = indexes.CharField(model_attr='description')

    def get_queryset(self):
        """Used when the entire index for model is updated."""
        # We also want to index past events in case a user wants to find
        # older events.
        # Inactive events should not be indexed
        return Event.active.all()

site.register(Event, EventIndex)
