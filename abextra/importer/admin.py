from django.contrib import admin

from autocomplete.views import autocomplete, AutocompleteSettings
from autocomplete.admin import AutocompleteAdmin

from importer.models import ExternalCategory, RegexCategory, EventExternalCats
from importer.models import ConditionalCategoryModel
from importer.forms import ExternalCategoryAdminForm
from events.models import Category

# class ExternalCategoryAutocomplete(AutocompleteSettings):
#     login_required = True
#     queryset = Category.objects.filter(category_type__in='CA')
#     search_fields = ('^title',)
# autocomplete.register(ExternalCategory.category, ExternalCategoryAutocomplete)

# class ExternalCategoryAdmin(AutocompleteAdmin, admin.ModelAdmin):
class ExternalCategoryAdmin(admin.ModelAdmin):
    form = ExternalCategoryAdminForm
    list_select_related = True
    fields = ('name', 'xid', 'source', 'concrete_category','abstract_categories')
    list_display = ('name', 'xid', 'source', 'concrete_category')
    list_filter = ('source', 'concrete_category')
    filter_horizontal = ('abstract_categories',)

admin.site.register(ExternalCategory, ExternalCategoryAdmin)


class SourceRegexAdmin(admin.ModelAdmin):
    model = RegexCategory
    list_display = ('source', 'regex', 'category', 'model_type')
    fields = ('source', 'regex', 'category', 'model_type')
    list_filter = ('source',)
    search_fields = ('source',)

admin.site.register(RegexCategory, SourceRegexAdmin)

class EventExternalCatAdmin(admin.ModelAdmin):
    model = EventExternalCats
    list_display = ('external_category', 'event',)
    fields = ('external_category', 'event',)
    list_filter = ('external_category__name',)
    search_fields = ('event',)

admin.site.register(EventExternalCats, EventExternalCatAdmin)

class ConditionalCategoryModelAdmin(admin.ModelAdmin):
    model = ConditionalCategoryModel
    list_display = ('conditional_category', 'regex', 'category')
    fields = ('conditional_category', 'regex', 'category')
    list_filter = ('conditional_category', 'regex')
    search_fields = ('regex',)

admin.site.register(ConditionalCategoryModel, ConditionalCategoryModelAdmin)
