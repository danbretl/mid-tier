import uuid
import hmac
from hashlib import sha1
from django.contrib.auth.models import User
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
