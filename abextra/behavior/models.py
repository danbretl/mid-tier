from django.db import models
from django.contrib.auth.models import User
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