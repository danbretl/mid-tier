from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.authorization import DjangoAuthorization

from api.authentication import ConsumerApiKeyAuthentication

from prices.models import Price

class PriceResource(ModelResource):
    class Meta:
        queryset = Price.objects.all()
        detail_allowed_methods = ()
        list_allowed_methods = ()
        authentication = ConsumerApiKeyAuthentication()
        authorization = DjangoAuthorization()
        fields = ('quantity', 'units', 'remark')
