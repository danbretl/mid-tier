from django.contrib import admin
from events.models import *


class SubcategoriesInline(admin.TabularInline):
    """Inline forms for subcategories"""
    model = Category
    fk = 'parent'

class CategoryAdmin(admin.ModelAdmin):
    search_fields = ('title',)
    # filter_horizontal = ('title',)
    list_display = ('title', 'parent', 'is_associative')
    inlines = [
        SubcategoriesInline
    ]

class EventTimeInline(admin.StackedInline):
    """Inline forms for event times"""
    model = EventTime
    fk = 'event'

class EventCategorizer(admin.ModelAdmin):
    """A skinny version of EventAdmin used for categorization parties"""
    search_fields = ('title',)
    fields = ('title', 'description', 'categories', 'one_off_place', 'url', 'image_url', 'video_url')
    readonly_fields = ('title', 'description','one_off_place', 'url', 'image_url', 'video_url')
    list_display = ('title', 'place', 'created')
    list_filter = ('one_off_place', 'image_url')
    filter_horizontal = ('categories',)

class EventAdmin(admin.ModelAdmin):
    """A full version of event administration form"""
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('categories',)
    list_display = ('title', 'place', 'created', 'cat_titles')
    list_filter = ('one_off_place',)
    inlines = [
        EventTimeInline
    ]

class ScrapedEventAdmin(admin.ModelAdmin):
    list_display = ('title',)
    # filter_horizontal = ('categories',)

admin.site.register(Category, CategoryAdmin)
# admin.site.register(Event, EventAdmin)
admin.site.register(Event, EventCategorizer)
# admin.site.register(ScrapedEvent, ScrapedEventAdmin)
