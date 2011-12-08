from django.contrib.auth.models import User
from django.db import models
from django.contrib.sites.models import Site
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.core.mail import send_mail
from django.conf import settings
from userena.models import UserenaBaseProfile
from userena.utils import get_protocol

class UserProfile(UserenaBaseProfile):
    ALPHA_STATUS_CHOICES = (
        ('P', 'Pending'),
        ('A', 'Approved'),
        ('D', 'Denied'),
    )
    alpha_status = models.CharField(max_length=1, choices=ALPHA_STATUS_CHOICES, null=True)
    user = models.OneToOneField(User, unique=True, verbose_name=_('user'), related_name='profile')
    facebook_id = models.CharField(max_length=25, null=True)

    def send_application_approved_email(self):
        context = {'user': self.user, 'protocol': get_protocol(), 'site': Site.objects.get_current()}

        subject = render_to_string('alphasignup/emails/application_approved_subject.txt', context)
        subject = ''.join(subject.splitlines())

        message = render_to_string('alphasignup/emails/application_approved_message.txt', context)
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [self.user.email, ])

    def send_application_denied_email(self):
        context = {'user': self.user, 'protocol': get_protocol(), 'site': Site.objects.get_current()}

        subject = render_to_string('alphasignup/emails/application_denied_subject.txt', context)
        subject = ''.join(subject.splitlines())

        message = render_to_string('alphasignup/emails/application_denied_message.txt', context)
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [self.user.email, ])
