from django.db import models
from django.contrib.auth.models import User
from events.models import Event, Category

class EventActionManager(models.Manager):
    def ignore_non_actioned_events(self, user, events):
        actioned_event_ids = user.event_actions.filter(event__in=events) \
            .values_list('event_id', flat=True)
        # FIXME since events are passed in as ids it's a bit inefficient
        events = Event.objects.filter(id__in=events)
        non_actioned_events = events.exclude(id__in=actioned_event_ids)
        for event in non_actioned_events:
            self.model(event=event, user=user, action='I').save()

class EventAction(models.Model):
    """Represents user's action on a particular event."""
    ACTION_CHOICES = (
        ('G', 'Went'),
        ('V', 'Viewed'),
        ('I', 'Ignored'),
        ('X', 'Deleted'),
    )
    user = models.ForeignKey(User, related_name='event_actions')
    event = models.ForeignKey(Event, related_name='actions')
    action = models.CharField(max_length=1, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now=True)

    objects = EventActionManager()

    class Meta:
        unique_together = (('user', 'event'),)
        ordering = ['timestamp']

    def __unicode__(self): return unicode(self.id or '?')

class EventActionAggregate(models.Model):
    """Helps store/retreive precomputed user_category_action aggregates."""
    user = models.ForeignKey(User)
    category = models.ForeignKey(Category)
    g = models.IntegerField(default=0, null=False)
    v = models.IntegerField(default=0, null=False)
    i = models.IntegerField(default=0, null=False)
    x = models.IntegerField(default=0, null=False)

    class Meta:
        unique_together = (('user', 'category'),)

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
# FIXME refactor for a bulk update  http://docs.djangoproject.com/en/1.2/topics/db/queries/#updating-multiple-objects-at-once
def update_aggregate_on_event_action_save(sender, instance, **kwargs):
    """
    Increases the aggregate count for a particular user's event action.
    Since, an event has multiple categories, we must update all aggregates
    accordingly.
    If event action is `fresh`, do a simple +1 count for the categories.
    If event action is a `change` of action, do a -1 count for the old action
    and +1 for the new action.
    """
    event_action = instance
    event_categories = set(event_action.event.categories.all())
    event_categories.add(event_action.event.concrete_category)

    # process existing aggregates
    aggregates = EventActionAggregate.objects.filter(
        user=event_action.user,
        category__in=event_categories
    )

    # get the old event action for this event from the db
    old_event_action = None
    if event_action.id:
        try:
            old_event_action = EventAction.objects.get(id=event_action.id) # FIXME select from the db twice
        except EventAction.DoesNotExist:
            pass

    # process existing aggregates
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

# FIXME pre_save is more fragile than post_save, but we need to grab the old action
models.signals.pre_save.connect(update_aggregate_on_event_action_save, sender=EventAction)


#def add_default_behavior(sender, instance, **kwargs):
#    user = User.objects.get(username='default_behavior')
#    EventActionAggregate.objects.get_or_create(user=user, category=instance)
#models.signals.post_save.connect(add_default_behavior, sender=Category)

# def update_aggregate_on_event_action_delete(sender, instance, **kwargs):
#     """Decreases aggregates after a deletion of event action."""
#     event_action = instance
#     aggregates = EventActionAggregate.objects.filter(
#         user=event_action.user,
#         category__in=event_action.event.categories.all()
#     )
#     for aggregate in aggregates:
#         aggregate.delete()
# 
# post_delete.connect(update_aggregate_on_event_action_delete, sender=EventAction)
