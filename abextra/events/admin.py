from django.contrib import admin
from django.template.defaultfilters import slugify
from events.models import Category, Event, Occurrence
from events.forms import CategoryAdminForm


class CategoriesInline(admin.TabularInline):
    """Inline forms for subcategories"""
    model = Category
    form = CategoryAdminForm
    extra = 0
    fields = ('title', 'is_associative', 'association_coefficient', 'icon')

class CategoryAdmin(admin.ModelAdmin):
    """Admin for categories"""
    form = CategoryAdminForm
    search_fields = ('title',)
    list_filter = ('category_type',)
    list_display = ('title', 'parent', 'category_type', 'is_associative')
    fields = ('parent', 'title', 'is_associative', 'association_coefficient', 'icon', 'icon_height', 'icon_width')
    readonly_fields = ('icon_height', 'icon_width')
    inlines = [
        CategoriesInline
    ]
admin.site.register(Category, CategoryAdmin)


class OccurrenceInline(admin.StackedInline):
    model = Occurrence
    fk = 'event'
    # fields = ('one_off_place',)
    # readonly_fields = ('one_off_place',)


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
