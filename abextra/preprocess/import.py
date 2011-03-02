from django.template.defaultfilters import slugify

from preprocess.models_external import Location as ExtLocation
from places.models import Place, Point, City

def persist_external_location(ext_location):
    # city
    city, created = City.objects.get_or_create(
        city=ext_location.city,
        state=ext_location.state,
        slug=slugify(u'-'.join((ext_location.city, ext_location.state)))
    )
    # point
    point, created = Point.objects.get_or_create(
        latitude=ext_location.latitude,
        longitude=ext_location.longitude,
        address=ext_location.address,
        city=city,
        zip=ext_location.zipcode,
        country='US'
    )
    # place
    place, created = Place.objects.get_or_create(
        point=point,
        # prefix = '',
        title=ext_location.title,
        slug=slugify(ext_location.title)[:50],
        # nickname=models.CharField(_('nickname'), blank=True, max_length=100),
        # unit=models.CharField(_('unit'), blank=True, max_length=100, help_text='Suite or Apartment #'),
        phone=ext_location.phone if ext_location.phone and (not ':' in ext_location.phone) else None or '',
        url=ext_location.url or ext_location.guid # FIXME source (villagevoice) specific
        # email=models.EmailField(_('email'), blank=True),
        # description = models.TextField(_('description'), blank=True),
        # status = models.IntegerField(_('status'), choices=STATUS_CHOICES, default=1)
        # created = models.DateTimeField(auto_now_add=True)
        # modified = models.DateTimeField(auto_now=True)
        # place_types = models.ManyToManyField(PlaceType, blank=True)
    )

class ImportLocations(object):
    def run(self):
        ext_locations = ExtLocation.objects.all()
        for ext_location in ext_locations:
            persist_external_location(ext_locations)
