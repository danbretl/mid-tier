from django.contrib import admin
from piston.models import Consumer


class ConsumerAdmin(admin.ModelAdmin):
    model = Consumer

admin.site.register(Consumer, Consumer)
admin.site.register(Category, CategoryAdmin)