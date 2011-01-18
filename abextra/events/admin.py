from django.contrib import admin
from events.models import *


class SubcategoriesInline(admin.TabularInline):
    model = Category
    fk = 'parent'

class CategoryAdmin(admin.ModelAdmin):
    model = Category
    list_display = ('title', 'parent', 'is_associative')
    inlines = [
        SubcategoriesInline
    ]

class EventTimeInline(admin.StackedInline):
    model = EventTime
    fk = 'event'

class EventAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
    list_display = ('title', 'place', 'created')
    filter_horizontal = ('categories',)
    inlines = [
        EventTimeInline
    ]

class ScrapedEventAdmin(admin.ModelAdmin):
    list_display = ('title',)
    # filter_horizontal = ('categories',)

admin.site.register(Category, CategoryAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(ScrapedEvent, ScrapedEventAdmin)
