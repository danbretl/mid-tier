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

class EventActionAggregate(models.Model):
    """Helps store/retreive precomputed user_category_action aggregates."""
    user = models.ForeignKey(User)
    category = models.ForeignKey(Category)
    g = models.IntegerField(default=0)
    v = models.IntegerField(default=0)
    i = models.IntegerField(default=0)
    x = models.IntegerField(default=0)
    c = models.FloatField(default=0.0)
