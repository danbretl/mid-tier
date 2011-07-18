from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.authorization import DjangoAuthorization
from api.authentication import ConsumerBasicAuthentication

from tastypie.models import ApiKey
from django.contrib.auth.models import User

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
