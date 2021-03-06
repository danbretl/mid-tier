from autoslug.fields import AutoSlugField
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.db.models import permalink
from django.contrib.localflavor.us import models as us_models
from django.contrib.gis.db import models as geo_models
from sorl.thumbnail import ImageField

class PlaceType(models.Model):
    """Place types model."""
    title = models.CharField(_('title'), max_length=100, unique=True)
    slug = models.SlugField(_('slug'), unique=True)

    class Meta:
        verbose_name = _('place type')
        verbose_name_plural = _('place types')

    def __unicode__(self):
        return u'%s' % self.title

    @permalink
    def get_absolute_url(self):
        return 'place_type_detail', None, {'slug': self.slug}


# FIXME two unique constraints impose two db checks for 'exists' validation
class City(models.Model):
    """City model"""
    city = models.CharField(_('city'), max_length=47)
    state = us_models.USStateField(_('state'))
    slug = AutoSlugField(_('slug'), editable=False,
         populate_from=lambda instance: '-'.join((instance.city, instance.state))
    )

    class Meta:
        verbose_name = _('city')
        verbose_name_plural = _('cities')
        unique_together = (('city', 'state'))

    def __unicode__(self):
        return u'%s, %s' % (self.city, self.state)

    @permalink
    def get_absolute_url(self):
        return 'place_city_detail', None, {'slug': self.slug}


class Point(geo_models.Model):
    """Point model"""
    geometry = geo_models.PointField(srid=4326)
    address = geo_models.CharField(_('address'), max_length=200, blank=True)
    city = geo_models.ForeignKey(City)
    zip = geo_models.CharField(_('zip'), max_length=10, blank=True)
    country = geo_models.CharField(_('country'), blank=True, max_length=100)

    objects = geo_models.GeoManager()

    class Meta:
        unique_together=(('address', 'city'))
        verbose_name = _('point')
        verbose_name_plural = _('points')
        ordering = ('address',)

    def __unicode__(self):
        return u'%s' % self.address


class Place(models.Model):
    """Place model."""
    STATUS_CHOICES = (
        (0, 'Inactive'),
        (1, 'Active'),
    )
    point = models.ForeignKey(Point)
    prefix = models.CharField(_('Pre-name'), blank=True, max_length=20)
    title = models.CharField(_('title'), max_length=255)
    slug = models.SlugField(_('slug'))
    nickname = models.CharField(_('nickname'), blank=True, max_length=100)
    unit = models.CharField(_('unit'), blank=True, max_length=100, help_text='Suite or Apartment #')
    phone = us_models.PhoneNumberField(_('phone'), blank=True)
    url = models.URLField(_('url'), blank=True, verify_exists=False)
    email = models.EmailField(_('email'), blank=True)
    description = models.TextField(_('description'), blank=True)
    status = models.IntegerField(_('status'), choices=STATUS_CHOICES, default=1)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    place_types = models.ManyToManyField(PlaceType, blank=True)
    image = ImageField(upload_to='location_images', blank=True, null=True)
    image_url = models.URLField(_('image_url'), blank=True, verify_exists=False)

    class Meta:
        unique_together = (('title', 'point'))
        verbose_name = _('place')
        verbose_name_plural = _('places')
        ordering = ('title',)

    def __unicode__(self):
        return u'%s' % self.full_title

    @property
    def city(self):
        return u'%s' % self.point.city

    @property
    def full_title(self):
        return u'%s %s' % (self.prefix, self.title)

    @permalink
    def get_absolute_url(self):
        return 'place_detail', None, { 'slug': self.slug }

    @property
    def longitude(self):
        return self.point.geometry.x

    @property
    def latitude(self):
        return self.point.geometry.y

    @property
    def address(self):
        return u'%s, %s %s' % (self.point.address, self.point.city, self.point.zip)