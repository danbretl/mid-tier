from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.authorization import DjangoAuthorization
from newapi.authentication import ConsumerAuthentication

from tastypie.models import ApiKey
from django.contrib.auth.models import User

class ApiKeyResource(ModelResource):
    class Meta:
        queryset = ApiKey.objects.all()
        allowed_methods = ('get')
        authentication = ConsumerAuthentication()
        authorization = DjangoAuthorization()
        fields = ('key',)

    def obj_get(self, request=None, **kwargs):
        udid = request.REQUEST.get('udid')
        import ipdb; ipdb.set_trace()
        return super(ApiKeyResource, self).obj_get(request, **kwargs)
