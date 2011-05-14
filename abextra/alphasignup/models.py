from django.db import models
from django.utils.translation import ugettext_lazy as _

from accounts.models import UserProfile

class AlphaQuestionnaire(models.Model):
    DEVICE_PLATFORM_CHOICES = (
        ('I', 'Apple iOS'),
        ('A', 'Android'),
        ('B', 'Blackberry'),
        ('P', 'Palm'),
        ('W', 'WinMobil'),
        ('O', 'None or Other'),
    )
    BOOL_CHOICES = ((True, 'Yes'), (False, 'No'))

    device_platform = models.CharField(max_length=1, choices=DEVICE_PLATFORM_CHOICES)
    zip = models.CharField(_('zip'), max_length=10, blank=True)
    is_usage_info_ok = models.BooleanField(default=False, choices=BOOL_CHOICES)
    is_mobile_planner = models.BooleanField(default=False, choices=BOOL_CHOICES)
    is_app_dev = models.BooleanField(default=False, choices=BOOL_CHOICES)
    year_of_birth = models.IntegerField()

    profile = models.OneToOneField(UserProfile, related_name='alpha_questionnaire')

    def _user_email(self):
        return self.profile.user.email
    _user_email.admin_order_field = 'profile__user__email'

    def _user_full_name(self):
        return self.profile.user.get_full_name()
    _user_full_name.admin_order_field = 'profile__user__last_name'

    def _user_alpha_status(self):
        return dict(self.profile.ALPHA_STATUS_CHOICES)[self.profile.alpha_status]
    _user_alpha_status.admin_order_field = 'profile__alpha_status'

    def _user_device_udid(self):
        return self.profile.user.device_udid.udid
    _user_device_udid.admin_order_field = 'profile__user__device_udid__udid'
