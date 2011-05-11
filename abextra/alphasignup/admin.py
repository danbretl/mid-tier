from django.contrib import admin
from alphasignup.models import AlphaQuestionnaire
from alphasignup.forms import AlphaQuestionnaireAdminForm

class AlphaQuestionnaireAdmin(admin.ModelAdmin):
    """Admin for alpha questionnaires"""
    form = AlphaQuestionnaireAdminForm
    # fields = ('profile__user',)
    # list_filter = ('category_type',)
    # list_display = ('title', 'parent_title', 'category_type', 'is_associative', 'icon')
    # fields = ()
    # inlines = [
    #     CategoriesInline
    # ]
admin.site.register(AlphaQuestionnaire, AlphaQuestionnaireAdmin)
