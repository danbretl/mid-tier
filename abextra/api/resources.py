from avatar.models import Avatar
from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.authorization import DjangoAuthorization
from api.authentication import ConsumerBasicAuthentication, ConsumerApiKeyAuthentication

from tastypie.models import ApiKey
from accounts.models import UserProfile

# ===========================
# = ApiKey Resource | Login =
# ===========================
class ApiKeyResource(ModelResource):
    full_name = fields.CharField(attribute='full_name', null=True)

    class Meta:
        queryset = ApiKey.objects.all()
        list_allowed_methods = ('get')
        detail_allowed_methods = ()
        authentication = ConsumerBasicAuthentication()
        authorization = DjangoAuthorization()
        fields = ('key',)
        resource_name = 'login'

    def get_object_list(self, request):
        """overridden to select relatives"""
        return super(ApiKeyResource, self).get_object_list(request) \
            .filter(user=request.user)

    def dehydrate_full_name(self, bundle):
        return bundle.obj.user.get_full_name()


class UserProfileResource(ModelResource):
    first_name = fields.CharField(attribute='first_name', null=True)
    last_name = fields.CharField(attribute='last_name', null=True)
    email = fields.CharField(attribute='email', null=True)
    avatar = fields.CharField(attribute='avatar', null=True)

    class Meta:
        queryset = UserProfile.objects.all()
        list_allowed_methods = ('get')
        detail_allowed_methods = ()
        authentication = ConsumerApiKeyAuthentication()
        authorization = DjangoAuthorization()
        fields = ('first_name', 'last_name', 'email')
        resource_name = 'userprofile'

    def dehydrate_email(self, bundle):
        return bundle.obj.user.email

    def dehydrate_first_name(self, bundle):
        return bundle.obj.user.first_name

    def dehydrate_last_name(self, bundle):
        return bundle.obj.user.last_name

    def dehydrate_avatar(self, bundle):
        try:
            primary_avatar = Avatar.objects.get(user=bundle.obj.user, primary=True)
        except Avatar.DoesNotExist, Avatar.MultipleObjectsReturned:
            return None
        else:
            return primary_avatar.avatar.url

    def get_object_list(self, request):
        """overridden to select relatives"""
        return super(UserProfileResource, self).get_object_list(request) \
            .select_related('user')

    def apply_authorization_limits(self, request, object_list):
        """limits qs to only the request user's objects"""
        return object_list.filter(user=request.user)
