from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from events.models import Event, Category

class EventAction(models.Model):
    """Represents user's action on a particular event."""
    ACTION_CHOICES = (
        ('G', 'Went'),
        ('V', 'Viewed'),
        ('I', 'Ignored'),
        ('X', 'Deleted'),
    )
    user = models.ForeignKey(User)
    event = models.ForeignKey(Event)
    action = models.CharField(max_length=1, choices=ACTION_CHOICES)

    def __unicode__(self): return unicode(self.id or '?')

class EventActionAggregate(models.Model):
    """Helps store/retreive precomputed user_category_action aggregates."""
    user = models.ForeignKey(User)
    category = models.ForeignKey(Category)
    g = models.IntegerField(default=0, null=False)
    v = models.IntegerField(default=0, null=False)
    i = models.IntegerField(default=0, null=False)
    x = models.IntegerField(default=0, null=False)

    def __unicode__(self): return unicode(self.id or '?')

    def update_action_count(self, action, delta=1, commit=False):
        # using reflection, set appropriate aggregate attribute
        action_attr = action.lower()
        updated_action_value = getattr(self, action_attr) + delta
        setattr(self, action_attr, updated_action_value)
        if commit:
            self.save()
        return self

# ---- signals ----

# FIXME needs to be much more optimized
# FIXME indexes on `action aggregate`{user_id, category_id}
# FIXME eager event / category related fields, see .defer
# FIXME refactor for a bulk update
def update_aggregate_behavior_sig_hangler(sender, instance, **kwargs):
    """
    Increases the aggregate count for a particular user's event action.
    Since, an event has multiple categories, we must update all aggregates
    accordingly.
    If event action is `fresh`, do a simple +1 count for the categories.
    If event action is a `change` of action, do a -1 count for the old action
    and +1 for the new action.
    """
    # import ipdb; ipdb.set_trace()
    event_action = instance
    event_categories = set(event_action.event.categories.all())

    # process existing aggregates
    aggregates = EventActionAggregate.objects.filter(
        user=event_action.user,
        category__in=event_categories
    )

    old_event_action = None
    if event_action.id:
        try:
            old_event_action = EventAction.objects.get(id=event_action.id) # FIXME select from the db twice
        except EventAction.DoesNotExist:
            pass

    for aggregate in aggregates:
        event_categories.remove(aggregate.category)
        if old_event_action:
            aggregate.update_action_count(old_event_action.action, delta=-1, commit=False)
        aggregate.update_action_count(event_action.action, commit=True)

    # process new aggregates (remaining in event categories)
    for category in event_categories:
        aggregate = EventActionAggregate(
            user=event_action.user,
            category=category
        ).update_action_count(event_action.action, commit=True)

pre_save.connect(update_aggregate_behavior_sig_hangler, sender=EventAction)
