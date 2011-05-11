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
