from django.db import models
from userena.models import UserenaBaseProfile

class UserProfile(UserenaBaseProfile):
    DEVICE_PLATFORM_CHOICES = (
        ('I', 'Apple iOS'),
        ('A', 'Android'),
        ('W', 'WinMobil'),
        ('O', 'Other'),
    )
    device_platform = models.CharField(max_length=1, choices=DEVICE_PLATFORM_CHOICES, blank=True)

    is_alpha_approved = models.BooleanField(default=False)
    is_nyc_resident = models.BooleanField(default=False)
    