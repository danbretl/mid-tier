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
    inlines = [
        SubcategoriesInline
    ]
admin.site.register(Category, CategoryAdmin)

# class EventTimeInline(admin.StackedInline):
#     """Inline forms for event times"""
#     model = EventTime
#     fk = 'occurrence'
# 
# class OccurrenceInline(admin.StackedInline):
#     model = Occurrence
#     fk = 'event'
# 
# class EventCategorizer(admin.ModelAdmin):
#     """A skinny version of EventAdmin used for categorization parties"""
#     search_fields = ('title',)
#     fields = ('title', 'description', 'categories', 'url', 'image_url', 'video_url')
#     readonly_fields = ('title', 'description', 'url', 'image_url', 'video_url')
#     list_display = ('title', 'place', 'created')
#     list_filter = ('image_url')
#     filter_horizontal = ('categories',)
# admin.site.register(Event, EventCategorizer)
# 
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
# 
# class ScrapedEventAdmin(admin.ModelAdmin):
#     list_display = ('title',)
#     # filter_horizontal = ('categories',)
