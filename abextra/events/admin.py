from django.contrib import admin
from events.models import *

class SubcategoriesInline(admin.TabularInline):
    """Inline forms for subcategories"""
    model = Category
    fk = 'parent'

class CategoryAdmin(admin.ModelAdmin):
    """Admin for categories"""
    search_fields = ('title',)
    # filter_horizontal = ('title',)
    list_display = ('title', 'parent', 'is_associative')
    fields = ('title', 'parent', 'is_associative', 'association_coefficient', 'icon', 'icon_height', 'icon_width')
    readonly_fields = ('icon_height', 'icon_width')
    inlines = [
        SubcategoriesInline
    ]
admin.site.register(Category, CategoryAdmin)

# FIXME currently, django does not support nested inlines http://code.djangoproject.com/ticket/9025
class EventTimeInline(admin.StackedInline):
    """Inline forms for event times"""
    model = EventTime
    fk = 'occurrence'

class OccurrenceInline(admin.StackedInline):
    model = Occurrence
    fk = 'event'
    fields = ('one_off_place',)
    readonly_fields = ('one_off_place',)
    inlines = [
        EventTimeInline
    ]

class EventCategorizer(admin.ModelAdmin):
    """A skinny version of EventAdmin used for categorization parties"""
    search_fields = ('title',)
    fields = ('title', 'description', 'categories', 'url', 'image_url', 'video_url')
    readonly_fields = ('title', 'description', 'url', 'image_url', 'video_url')
    list_display = ('title', 'created')
    list_filter = ('image_url',)
    filter_horizontal = ('categories',)
    inlines = [
        OccurrenceInline
    ]
admin.site.register(Event, EventCategorizer)

# class EventAdmin(admin.ModelAdmin):
#     """A full version of event administration form"""
#     search_fields = ('title',)
#     prepopulated_fields = {'slug': ('title',)}
#     filter_horizontal = ('categories',)
#     list_display = ('title', 'place', 'created', 'cat_titles')
#     list_filter = ('one_off_place',)
#     inlines = [
#         EventTimeInline
#     ]
# # admin.site.register(Event, EventAdmin)