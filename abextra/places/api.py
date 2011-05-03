from tastypie import fields
from tastypie.resources import ModelResource
from places.models import Place, Point, City
from tastypie.authorization import DjangoAuthorization

from newapi.authentication import ConsumerApiKeyAuthentication

# ========
# = City =
# ========
class CityResource(ModelResource):
    class Meta:
        queryset = City.objects.all()
        allowed_methods = ('get',)
        list_allowed_methods = ()
        authentication = ConsumerApiKeyAuthentication()
        fields = ('city', 'state')

# =========
# = Point =
# =========
class PointResource(ModelResource):
    city = fields.ToOneField(CityResource, 'city')

    class Meta:
        queryset = Point.objects.all()
        allowed_methods = ('get',)
        list_allowed_methods = ()
        authentication = ConsumerApiKeyAuthentication()
        fields = ('city',
            'latitude', 'longitude', 'address', 'zip', 'country'
        )

class PointFullResource(PointResource):
    city = fields.ToOneField(CityResource, 'city', full=True)

    class Meta(PointResource.Meta):
        resource_name = 'point_full'

# =========
# = Place =
# =========
class PlaceResource(ModelResource):
    point = fields.ToOneField(PointResource, 'point')

    class Meta:
        queryset = Place.objects.all()
        allowed_methods = ('get',)
        list_allowed_methods = ()
        authentication = ConsumerApiKeyAuthentication()
        fields = ('point',
            'title', 'description', 'unit', 'phone', 'url', 'email', 'image',
        )

class PlaceFullResource(PlaceResource):
    point = fields.ToOneField(PointFullResource, 'point', full=True)

    class Meta(PlaceResource.Meta):
        resource_name = 'place_full'
