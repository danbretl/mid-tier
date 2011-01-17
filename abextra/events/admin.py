from django.contrib import admin
from events.models import *


class EventTimeInline(admin.StackedInline):
    model = EventTime
    fk = 'event'

class SubcategoriesInline(admin.StackedInline):
    model = Category
    fk = 'parent'

class CategoryAdmin(admin.ModelAdmin):
    model = Category
    inlines = [
        SubcategoriesInline
    ]


class EventAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
    list_display = ('title', 'place', 'created')
    inlines = [
        EventTimeInline
    ]
admin.site.register(Event, EventAdmin)
admin.site.register(Category, CategoryAdmin)