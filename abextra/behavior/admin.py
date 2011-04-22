from django.contrib import admin
from behavior.models import *

class EventActionAdmin(admin.ModelAdmin):
    """A full version of event administration form"""
    list_display = ('user', 'event', 'timestamp', 'action')
    # This filter will be painful if we have too many users. 
    list_filter = ('user', 'action')
admin.site.register(EventAction, EventActionAdmin)

class EventActionAggregateAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'g', 'v', 'i', 'x')
    fields = ('user', 'category', 'g', 'v', 'i', 'x')
admin.site.register(EventActionAggregate, EventActionAggregateAdmin)
