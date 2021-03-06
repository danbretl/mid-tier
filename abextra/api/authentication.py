import base64
from tastypie.authentication import Authentication, BasicAuthentication, ApiKeyAuthentication
from tastypie.http import HttpUnauthorized
from tastypie.models import ApiKey
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.forms import ValidationError

from models import Consumer, DeviceUdid
from forms import DeviceUdidForm

class ConsumerAuthentication(Authentication):
    def _unauthorized(self):
        return HttpUnauthorized()

    def is_authenticated(self, request, **kwargs):
        consumer_key, consumer_secret = map(request.REQUEST.get, ('consumer_key', 'consumer_secret'))

        if not all((consumer_key, consumer_secret)):
            return self._unauthorized()

        try:
            consumer = Consumer.objects.select_related('user').get(
                key=consumer_key, secret=consumer_secret, is_active=True
            )
        except Consumer.DoesNotExist, Consumer.MultipleObjectsReturned:
            return self._unauthorized()
        else:
            request.user = consumer.user

        # ancestor will always return True
        return super(ConsumerAuthentication, self).is_authenticated(request, **kwargs)

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
            udid = DeviceUdid.objects.select_related('user_anonymous').get(
                udid=raw_udid
                # udid=DeviceUdid.objects.get_hexdigest(raw_udid)   # doing raw
            )
        except (DeviceUdid.DoesNotExist, DeviceUdid.MultipleObjectsReturned):
            udid = DeviceUdid.objects.create_udid_and_user(raw_udid)
        request.user = udid.user_anonymous

        # authenticate api key
        if api_key:
            try:
                key = ApiKey.objects.select_related('user').get(key=api_key)
            except ApiKey.DoesNotExist:
                return self._unauthorized()
            else:
                request.user = key.user

        return True


# ========================
# = Custom Auth Backends =
# ========================
class BasicBackend:
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class EmailBackend(BasicBackend):
    def authenticate(self, username=None, password=None):
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            return None
        if user.check_password(password):
            return user

    def user_exists(self, username):
        return User.objects.filter(email=username).exists()


class VerboseBasicAuthentication(BasicAuthentication):
    def is_authenticated(self, request, **kwargs):
        """
        Taken directly from Tastypie, to add the differentiation between
        unregistered emails and failed account/pass authentication.
        ---
        Should return either ``True`` if allowed, ``False`` if not or an
        ``HttpResponse`` if you need something custom.
        """
        if not request.META.get('HTTP_AUTHORIZATION'):
            return self._unauthorized()

        try:
            (auth_type, data) = request.META['HTTP_AUTHORIZATION'].split()
            if auth_type != 'Basic':
                return self._unauthorized()
            user_pass = base64.b64decode(data)
        except Exception:
            return self._unauthorized()

        bits = user_pass.split(':')

        if len(bits) != 2:
            return self._unauthorized()

        if self.backend:
            user = self.backend.authenticate(username=bits[0], password=bits[1])
        else:
            user = authenticate(username=bits[0], password=bits[1])

        if user is None:
            if hasattr(self.backend, 'user_exists'):
                user_exists = self.backend.user_exists(username=bits[0])
                if user_exists:
                    # user exists but unsuccessful auth
                    return self._unauthorized()
            response = self._unauthorized()
            response.write('NOT REGISTERED')
            return response

        request.user = user
        return True


class ConsumerBasicAuthentication(VerboseBasicAuthentication):
    def __init__(self, backend=EmailBackend(), realm='kwiqet-mobile'):
        super(ConsumerBasicAuthentication, self).__init__(backend, realm)

    def is_authenticated(self, request, **kwargs):
        consumer_key = request.REQUEST.get('consumer_key')
        consumer_secret = request.REQUEST.get('consumer_secret')

        if not consumer_key or not consumer_secret:
            return self._unauthorized()

        consumer_exists = Consumer.objects.select_related('user').filter(
            key=consumer_key, secret=consumer_secret, is_active=True
        ).exists()
        if not consumer_exists:
            return self._unauthorized()

        # ancestor will always return True
        return super(ConsumerBasicAuthentication, self).is_authenticated(request, **kwargs)
