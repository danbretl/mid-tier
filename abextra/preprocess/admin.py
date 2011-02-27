from django.contrib import admin
from preprocess import models, forms

class ScrapedEventAdmin(admin.ModelAdmin):
    list_display = ('title',)
    # filter_horizontal = ('categories',)
admin.site.register(models.ScrapedEvent, ScrapedEventAdmin)

class SourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'domain')
admin.site.register(models.Source, SourceAdmin)

class ExternalCategoryAdmin(admin.ModelAdmin):
    form = forms.ExternalCategoryAdminForm
    fields = ('name', 'xid', 'source', 'category')
    list_display = ('name', 'xid', 'source', 'category')
    list_filter = ('source',)
admin.site.register(models.ExternalCategory, ExternalCategoryAdmin)
