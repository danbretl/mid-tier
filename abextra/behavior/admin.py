from django.contrib import admin
from behavior.models import *


class EventActionAdmin(admin.ModelAdmin):
    """A full version of event administration form"""
    list_display = ('user', 'event', 'action')

admin.site.register(EventAction, EventActionAdmin)
