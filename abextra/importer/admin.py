from django.contrib import admin

from autocomplete.views import autocomplete, AutocompleteSettings
from autocomplete.admin import AutocompleteAdmin

from importer.models import ExternalCategory, RegexCategory
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



