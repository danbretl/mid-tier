from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _

class UserProfile(models.Model):
    user = models.OneToOneField(User, unique=True, verbose_name=_('user'), related_name='profile')
