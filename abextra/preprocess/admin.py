from django.contrib import admin

from autocomplete.views import autocomplete, AutocompleteSettings
from autocomplete.admin import AutocompleteAdmin

from preprocess import models, forms
from events.models import Category

class ScrapedEventAdmin(admin.ModelAdmin):
    list_display = ('title',)
    # filter_horizontal = ('categories',)
admin.site.register(models.ScrapedEvent, ScrapedEventAdmin)

class SourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'domain')
admin.site.register(models.Source, SourceAdmin)


external_categories_autocomplete_settings = AutocompleteSettings
external_categories_autocomplete_settings.login_required = True

class ExternalCategoryAutocomplete(external_categories_autocomplete_settings):
    queryset = Category.objects.filter(category_type__in='CA')
    search_fields = ('^title',)
autocomplete.register(models.ExternalCategory.category, ExternalCategoryAutocomplete)

class ExternalCategoryAdmin(AutocompleteAdmin,admin.ModelAdmin):
    # form = forms.ExternalCategoryAdminForm
    fields = ('name', 'xid', 'source', 'category')
    list_display = ('name', 'xid', 'source', 'category')
    list_filter = ('source',)
admin.site.register(models.ExternalCategory, ExternalCategoryAdmin)
