from django.contrib import admin
from models import ScrapedEvent

class ScrapedEventAdmin(admin.ModelAdmin):
    list_display = ('title',)
    # filter_horizontal = ('categories',)
admin.site.register(ScrapedEvent, ScrapedEventAdmin)
