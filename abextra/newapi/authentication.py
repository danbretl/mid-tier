from tastypie.authentication import Authentication, ApiKeyAuthentication
from tastypie.http import HttpUnauthorized
from utils import validate_iphone_udid

from django.contrib.auth.models import User, Group
from models import Consumer, DeviceUdid

class ConsumerAuthentication(Authentication):
    def _unauthorized(self):
        return HttpUnauthorized()

    def is_authenticated(self, request, **kwargs):
        consumer_key = request.REQUEST.get('consumer_key')
        consumer_secret = request.REQUEST.get('consumer_secret')

        if not consumer_key or not consumer_secret:
            return self._unauthorized()

        try:
            consumer = Consumer.objects.select_related('user').get(
                key=consumer_key, secret=consumer_secret, is_active=True
            )
        except (Consumer.DoesNotExist, Consumer.MultipleObjectsReturned):
            return self._unauthorized()
        else:
            request.user = consumer.user

        # ancestor will always return True
        return super(ConsumerAuthentication, self) \
            .is_authenticated(request, **kwargs)

    def get_identifier(self, request):
        base = super(ConsumerAuthentication, self).get_identifier(request)
        return '_'.join((base, request.REQUEST.get('consumer_key', 'noconsumer')))


class ConsumerApiKeyAuthentication(ApiKeyAuthentication):
    def is_authenticated(self, request, **kwargs):
        consumer_key = request.REQUEST.get('consumer_key')
        consumer_secret = request.REQUEST.get('consumer_secret')
        raw_udid = request.REQUEST.get('udid')

        # check for all required authentication pieces
        # FIXME make udid optional -> consumer should dictate this
        if not consumer_key or not consumer_secret or not raw_udid:
            return self._unauthorized()

        # authenticate consumer
        try:
            consumer = Consumer.objects.select_related('user').get(
                key=consumer_key, secret=consumer_secret, is_active=True
            )
        except (Consumer.DoesNotExist, Consumer.MultipleObjectsReturned):
            return self._unauthorized()
        else:
            request.user = consumer.user

        # authenticate device
        api_key = request.REQUEST.get('api_key')
        if validate_iphone_udid(raw_udid) and not api_key:
            try:
                udid = DeviceUdid.objects.select_related('user').get(
                    udid=raw_udid
                )
            except (DeviceUdid.DoesNotExist, DeviceUdid.MultipleObjectsReturned):
                # create new user
                user = User()
                user.username = 'udid_user$' + User.objects.make_random_password(length=20)
                user.set_password(None)     # makes unusable password
                user.save()

                # create device udid record
                udid = DeviceUdid(user=user, udid=raw_udid).save()

                # add to proper user group
                group = Group.objects.get(name='device_user_anonymous')
                user.groups.add(group)

                request.user = user
            else:
                request.user = udid.user
            return True

        # authenticate user by api key
        return super(ConsumerApiKeyAuthentication, self) \
            .is_authenticated(request, **kwargs)
