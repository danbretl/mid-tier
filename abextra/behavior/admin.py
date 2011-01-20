from django.contrib import admin
from behavior.models import *

class EventActionAdmin(admin.ModelAdmin):
    """A full version of event administration form"""
    list_display = ('user', 'event', 'action')
admin.site.register(EventAction, EventActionAdmin)

class EventActionAggregateAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'g', 'v', 'i', 'x', 'c')
    fields = ('user', 'category', 'g', 'v', 'i', 'x', 'c')
admin.site.register(EventActionAggregate, EventActionAggregateAdmin)
