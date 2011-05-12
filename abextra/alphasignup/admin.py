from django.contrib import admin
from alphasignup.models import AlphaQuestionnaire

class AlphaQuestionnaireAdmin(admin.ModelAdmin):
    """Admin for alpha questionnaires"""
    model = AlphaQuestionnaire
    fields = ('device_platform', 'zip', 'is_usage_info_ok', 'is_mobile_planner', 'is_app_dev', 'year_of_birth')
    readonly_fields = ('device_platform', 'zip', 'is_usage_info_ok', 'is_mobile_planner', 'is_app_dev', 'year_of_birth')
    list_display = ('profile',)
    list_filter = ('profile__alpha_status',)
    actions = ('APPROVE', 'DENY')

    def APPROVE(self, request, queryset):
        for q in queryset.select_related('profile'):
            profile = q.profile
            profile.alpha_status = 'A'  # approved
            profile.save()
            profile.send_application_approved_email()
        self.message_user(request, "Alpha applications successfully approved.")

    def DENY(self, request, queryset):
        for q in queryset.select_related('profile'):
            profile = q.profile
            profile.alpha_status = 'D'  # denied
            profile.save()
            profile.send_application_denied_email()
        self.message_user(request, "Alpha applications successfully denied.")

admin.site.register(AlphaQuestionnaire, AlphaQuestionnaireAdmin)
