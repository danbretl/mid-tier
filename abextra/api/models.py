import uuid
import hmac
import re
from hashlib import sha1
from django.contrib.auth.models import User, Group
from django.db import models

KEY_SIZE = 18

class ConsumerManager(models.Manager):

    def create_consumer(self, name, is_active=False):
        """Shortcut to create a consumer with random key/secret."""
        consumer, created = self.get_or_create(
            name=name
        )

        if created:
            consumer.is_active = is_active
            consumer.key = self.generate_key()
            consumer.secret = self.generate_secret()
            consumer.user = User.objects.get(username='consumer_iphone')

        consumer.save()
        return consumer

    def generate_key(self):
        make_key = lambda: User.objects.make_random_password(length=KEY_SIZE)
        key = make_key()
        while self.filter(key=key).count():
            key = make_key()
        return key

    def generate_secret(self):
        new_uuid = uuid.uuid4()
        return hmac.new(str(new_uuid), digestmod=sha1).hexdigest()

class Consumer(models.Model):
    name = models.CharField(max_length=20, unique=True)
    key = models.CharField(max_length=KEY_SIZE, unique=True)
    secret = models.CharField(max_length=40)
    user = models.ForeignKey(User, related_name='consumers_tasty')
    is_active = models.BooleanField(default=False)

    objects = ConsumerManager()

    def __unicode__(self):
        return u"Consumer %s with key %s" % (self.name, self.key)

# ===============
# = Device UDID =
# ===============
from django.utils.crypto import salted_hmac

class DeviceUdidManager(models.Manager):
    udid_re = re.compile(
        r'([0-9A-F]{8}(-[0-9A-F]{4}){3}-[0-9A-F]{12})|([0-9A-F]{40})', re.I
    )

    def get_hexdigest(self, raw_udid):
        salt = 'QJ7@cqBQdLy$mqr+'
        hmac = salted_hmac(salt, raw_udid)
        return hmac.hexdigest()

    def generate_username(self, prefix='udid', rand_length=20):
        return '_'.join(
            (prefix, User.objects.make_random_password(rand_length))
        )

    def generate_username_unique(self, prefix='udid', rand_length=20):
        new_username = self.generate_username(prefix=prefix, rand_length=rand_length)
        while User.objects.filter(username=new_username).exists():
            new_username = self.generate_username(prefix=prefix, rand_length=rand_length)
        return new_username

    def create_anonymous_user(self):
        username_anonymous = self.generate_username_unique()
        user_anonymous = User.objects.create_user(
            username=username_anonymous, email=''
        )
        # add to proper user group
        group = Group.objects.get(name='device_user_anonymous')
        user_anonymous.groups.add(group)
        return user_anonymous

    def create_udid_and_user(self, raw_udid):
        re_result = self.udid_re.search(raw_udid)
        if re_result:
            user_anonymous = self.create_anonymous_user()
            udid = self.create(udid=re_result.group(), user_anonymous=user_anonymous)
            return udid

class DeviceUdid(models.Model):
    user = models.OneToOneField(User, related_name='device_udid', null=True, blank=True)
    udid = models.CharField(max_length=40, unique=True)
    users = models.ManyToManyField(User, related_name='device_udids')
    user_anonymous = models.OneToOneField(User, related_name='device_udid_anonymous', null=True, blank=True)

    objects = DeviceUdidManager()

    def __unicode__(self):
        return u"%s for %s" % (self.udid, self.user)
