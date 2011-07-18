from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.db.models import permalink
from django.contrib.localflavor.us import models as us_models
from sorl.thumbnail import ImageField




class PlaceType(models.Model):
    """Place types model."""
    title = models.CharField(_('title'), max_length=100, unique=True)
    slug = models.SlugField(_('slug'), unique=True)
    concrete_category = models.ForeignKey('events.Category',
                                          related_name='place_concrete',
                                          null=True)
    abstract_categories = models.ManyToManyField('events.Category',
                                                 related_name='place_abstract',
                                                 verbose_name='abstract_categories',
                                                 null=True)

    class Meta:
        verbose_name = _('place type')
        verbose_name_plural = _('place types')

    def __unicode__(self):
        return u'%s' % self.title

    @permalink
    def get_absolute_url(self):
        return ('place_type_detail', None, {'slug': self.slug})


# FIXME two unique constraints impose two db checks for 'exists' validation
class City(models.Model):
    """City model."""
    city = models.CharField(_('city'), max_length=100)
    state = us_models.USStateField(_('state'))
    slug = models.SlugField(_('slug'), unique=True)

    class Meta:
        verbose_name = _('city')
        verbose_name_plural = _('cities')
        unique_together = (('city', 'state',),)
        ordering = ('state', 'city',)

    def __unicode__(self):
        return u'%s, %s' % (self.city, self.state)

    @permalink
    def get_absolute_url(self):
        return ('place_city_detail', None, {'slug': self.slug})


class Point(models.Model):
    """Point model."""
    latitude = models.FloatField(_('latitude'), blank=True, null=True)
    longitude = models.FloatField(_('longitude'), blank=True, null=True)
    address = models.CharField(_('address'), max_length=200, blank=True)
    city = models.ForeignKey(City)
    zip = models.CharField(_('zip'), max_length=10, blank=True)
    country = models.CharField(_('country'), blank=True, max_length=100)

    class Meta:
        verbose_name = _('point')
        verbose_name_plural = _('points')
       smart-operator: Automatically adds spaces around arithmetic operators. ordering = ('address',)

    def __unicode__(self):
        return u'%s' % self.address


# TODO don't need:  prefix, nickname
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
    concrete_category = models.ForeignKey('events.Category', related_name='places_concrete', null=True)
    abstract_categories = models.ManyToManyField('events.Category', related_name='places_abstract', verbose_name=_('abstract_categories'), null=True)

    class Meta:
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
        return ('place_detail', None, { 'slug': self.slug } )

    @property
    def longitude(self):
        return self.point.longitude

    @property
    def latitude(self):
        return self.point.latitude

    @property
    def address(self):
        return u'%s, %s %s' % (self.point.address, self.point.city, self.point.zip)
