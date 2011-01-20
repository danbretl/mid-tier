from django.db import models
from django.contrib.auth.models import User
from events.models import Event

class EventAction(models.Model):
    """Represents user's action on a particular event"""
    ACTION_CHOICES = (
        ('V', 'Viewed'),
        ('G', 'Went'),
        ('I', 'Ignored'),
        ('X', 'Deleted'),
    )
    user = models.ForeignKey(User)
    event = models.ForeignKey(Event)
    action = models.CharField(max_length=1, choices=ACTION_CHOICES)
