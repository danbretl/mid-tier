from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.authorization import DjangoAuthorization
from newapi.authentication import ConsumerApiKeyAuthentication

from prices.models import Price

class PriceResource(ModelResource):
    class Meta:
        queryset = Price.objects.all()
        allowed_methods = ('get',)
        list_allowed_methods = ()
        authentication = ConsumerApiKeyAuthentication()
        authorization = DjangoAuthorization()
        fields = ('quantity', 'units', 'remark')
