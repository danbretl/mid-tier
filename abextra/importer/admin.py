from django.contrib import admin

from autocomplete.views import autocomplete, AutocompleteSettings
from autocomplete.admin import AutocompleteAdmin

from importer.models import ExternalCategory
from importer.forms import ExternalCategoryAdminForm
from events.models import Category

class ExternalCategoryAutocomplete(AutocompleteSettings):
    login_required = True
    queryset = Category.objects.filter(category_type__in='CA')
    search_fields = ('^title',)
autocomplete.register(models.ExternalCategory.category, ExternalCategoryAutocomplete)

class ExternalCategoryAdmin(AutocompleteAdmin, admin.ModelAdmin):
    # form = ExternalCategoryAdminForm
    list_select_related = True
    list_display = ('name', 'xid', 'source', 'category_title')
    fields = ('name', 'xid', 'source', 'category')
    list_filter = ('source',)

    # def category(self, external_category):
    #     return external_category.category.title

admin.site.register(models.ExternalCategory, ExternalCategoryAdmin)
