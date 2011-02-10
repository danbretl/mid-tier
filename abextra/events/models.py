import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from places.models import Place


class Category(models.Model):
    """Category model"""
    TYPE_CHOICES = ( ('C', 'Concrete'), ('A', 'Abstract'), ('O', 'Other') )
    category_type = models.CharField(max_length=1, choices=TYPE_CHOICES)
    title = models.CharField(max_length=100, unique=True)
    parent = models.ForeignKey('self', related_name='subcategories', blank=True, null=True)
    is_associative = models.BooleanField(default=True)
    association_coefficient = models.FloatField(default=0)
    icon = models.ImageField(upload_to="category_icons", height_field='icon_height', width_field='icon_width', blank=True, null=True)
    icon_height = models.PositiveSmallIntegerField(blank=True, null=True)
    icon_width = models.PositiveSmallIntegerField(blank=True, null=True)

    @property
    def icon_path(self):
        return self.icon.name if self.icon else None

    class Meta:
        verbose_name_plural = _('categories')

    def __unicode__(self):
        return u'[%s] %s' % (self.id or '?', self.title)


class Event(models.Model):
    """Event model"""
    xid = models.CharField(_('external id'), max_length=200, blank=True)
    title = models.CharField(max_length=200)
    slug = models.SlugField()
    description = models.TextField(blank=True)
    submitted_by = models.ForeignKey(User, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    url = models.URLField(verify_exists=False, max_length=300)
    image_url = models.URLField(verify_exists=False, max_length=300, blank=True)
    video_url = models.URLField(verify_exists=False, max_length=200, blank=True)
    concrete_category = models.ForeignKey(Category, related_name='events_concrete', blank=True, null=True)
    categories = models.ManyToManyField(Category, verbose_name=_('event categories'), blank=True)

    class Meta:
        verbose_name_plural = _('events')


class Occurrence(models.Model):
    """Models a particular occurance of an event"""
    event = models.ForeignKey(Event, related_name='occurrences')
    place = models.ForeignKey(Place, blank=True, null=True)
    one_off_place = models.CharField(max_length=200, blank=True)
    start_date = models.DateField()
    start_time = models.TimeField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    is_all_day = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = _('occurrences')

    @property
    def is_past(self): pass

    @property
    def is_future(self): pass

    @property
    def is_now(self): pass
