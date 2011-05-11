from django.db import models
from userena.models import UserenaBaseProfile

class UserProfile(UserenaBaseProfile):
    ALPHA_STATUS_CHOICES = (
        ('P', 'Pending'),
        ('A', 'Approved'),
        ('D', 'Denied'),
    )
    alpha_status = models.CharField(max_length=1, choices=ALPHA_STATUS_CHOICES, null=True)
    