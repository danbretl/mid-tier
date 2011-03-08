from django.contrib import admin
from prices.models import Price

class PriceAdmin(admin.ModelAdmin):
    """Admin for prices"""
    fields = ('remark', 'quantity', 'units')
admin.site.register(Price, PriceAdmin)
