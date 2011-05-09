from django.db import models
from django.utils.translation import ugettext_lazy as _

from accounts.models import UserProfile

class AlphaQuestionnaire(models.Model):
    DEVICE_PLATFORM_CHOICES = (
        ('I', 'Apple iOS'),
        ('A', 'Android'),
        ('W', 'WinMobil'),
        ('O', 'Other'),
    )
    device_platform = models.CharField(max_length=1, choices=DEVICE_PLATFORM_CHOICES, blank=True)
    profile = models.OneToOneField(UserProfile, related_name='alpha_questionnaire')
    zip = models.CharField(_('zip'), max_length=10, blank=True)
    
