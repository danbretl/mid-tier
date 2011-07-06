from django.contrib import admin
from django.template.defaultfilters import slugify

from autocomplete.views import autocomplete, AutocompleteSettings
from autocomplete.admin import AutocompleteAdmin

from sorl.thumbnail.admin import AdminImageMixin

from events.models import Event, Category, Occurrence, Source
from events.forms import EventAdminForm, CategoryAdminForm, SourceAdminForm

# ============
# = Category =
# ============
class CategoriesInline(admin.TabularInline):
    """Inline forms for subcategories"""
    model = Category
    form = CategoryAdminForm
    extra = 0
    fields = ('title', 'is_associative', 'association_coefficient', 'icon')

class CategoryAdmin(AdminImageMixin, admin.ModelAdmin):
    """Admin for categories"""
    form = CategoryAdminForm
    search_fields = ('title',)
    list_filter = ('category_type',)
    list_display = ('title', 'parent_title', 'category_type', 'is_associative', 'icon')
    fields = ('parent', 'title', 'is_associative', 'association_coefficient', 'icon', 'thumb', 'color')
    inlines = [
        CategoriesInline
    ]
admin.site.register(Category, CategoryAdmin)

class CategoryAutocomplete(AutocompleteSettings):
    login_required = True
    queryset = Category.concrete.all()
    search_fields = ('^title',)
# autocomplete.register(Event.concrete_category, CategoryAutocomplete)

# ==============================
# = Event / Occurrence(inline) =
# ==============================
class OccurrenceInline(admin.StackedInline):
    model = Occurrence
    fk = 'event'
    extra = 0
    # fields = ('one_off_place',)
    # readonly_fields = ('one_off_place',)

class EventAdmin(AdminImageMixin, AutocompleteAdmin, admin.ModelAdmin):
    """A skinny version of EventAdmin used for categorization parties"""
    form = EventAdminForm
    search_fields = ('title',)
    fields = ('title', 'description', 'concrete_category', 'categories', 'is_active', 'url', 'image', 'video_url')
    readonly_fields = ('title', 'description', 'url', 'image_url', 'video_url',)
    list_display = ('title', 'created', '_concrete_category', '_abstract_categories')
    list_filter = ('concrete_category',)
    filter_horizontal = ('categories',)
    inlines = [
        OccurrenceInline
    ]
admin.site.register(Event, EventAdmin)

# ==========
# = Source =
# ==========
class SourceAdmin(admin.ModelAdmin):
    form = SourceAdminForm
    list_display = ('name', 'domain', 'default_concrete_category')
    fields = ('name', 'domain',
        'default_concrete_category', 'default_abstract_categories',
    )
admin.site.register(Source, SourceAdmin)
