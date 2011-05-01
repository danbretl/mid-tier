from tastypie.authentication import Authentication, ApiKeyAuthentication
from tastypie.http import HttpUnauthorized

from django.contrib.auth.models import User, Group
from django.forms import ValidationError

from models import Consumer, DeviceUdid
from forms import DeviceUdidForm

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
    udid_field = DeviceUdidForm.declared_fields['udid']

    def is_authenticated(self, request, **kwargs):
        consumer_key = request.REQUEST.get('consumer_key')
        consumer_secret = request.REQUEST.get('consumer_secret')
        raw_udid = request.REQUEST.get('udid')
        api_key = request.REQUEST.get('api_key')

        # check for all required authentication pieces
        # FIXME make udid optional -> consumer should dictate this
        if not consumer_key or not consumer_secret or not raw_udid:
            return self._unauthorized()
        try:
            raw_udid = self.udid_field.clean(raw_udid)
        except ValidationError:
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
        try:
            udid = DeviceUdid.objects.select_related('user').get(
                udid=DeviceUdid.objects.get_hexdigest(raw_udid)
            )
        except (DeviceUdid.DoesNotExist, DeviceUdid.MultipleObjectsReturned):
            # create new user
            username = DeviceUdid.objects.generate_username_unique()
            new_user = User.objects.create_user(username=username, email='')

            # create device udid record
            udid_form = DeviceUdidForm(data=dict(user=new_user.id, udid=raw_udid))
            if udid_form.is_valid():
                udid = udid_form.save()

            # add to proper user group
            group = Group.objects.get(name='device_user_anonymous')
            new_user.groups.add(group)

            request.user = new_user
        else:
            request.user = udid.user

        # authenticate user by api key
        return super(ConsumerApiKeyAuthentication, self) \
            .is_authenticated(request, **kwargs) if api_key else True
