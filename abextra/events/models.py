import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.db.models import permalink
from django.contrib.auth.models import User
from places.models import Place


class Category(models.Model):
    """Category model"""
    title = models.CharField(max_length=100)
    parent = models.ForeignKey('self', related_name='subcategories', blank=True, null=True)
    is_associative = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = _('categories')

    def __unicode__(self):
        return u'%s' % self.title

class ScrapedEvent(models.Model):
    """Directly from the scrape db"""
    internalid = models.IntegerField(primary_key=True, db_column='InternalID') # Field name made lowercase.
    title = models.CharField(max_length=600, db_column='Title', blank=True) # Field name made lowercase.
    externalid = models.CharField(max_length=90, db_column='ExternalID', blank=True) # Field name made lowercase.
    eventdate = models.DateField(null=True, db_column='EventDate', blank=True) # Field name made lowercase.
    starttime = models.DateTimeField(db_column='StartTime') # Field name made lowercase.
    endtime = models.DateTimeField(db_column='EndTime') # Field name made lowercase.
    description = models.CharField(max_length=9000, db_column='Description', blank=True) # Field name made lowercase.
    url = models.CharField(max_length=600, db_column='URL', blank=True) # Field name made lowercase.
    imageurl = models.CharField(max_length=600, db_column='ImageURL', blank=True) # Field name made lowercase.
    videourl = models.CharField(max_length=600, db_column='VideoURL', blank=True) # Field name made lowercase.
    location = models.CharField(max_length=600, db_column='Location', blank=True) # Field name made lowercase.
    email = models.CharField(max_length=150, db_column='Email', blank=True) # Field name made lowercase.
    phone = models.CharField(max_length=45, db_column='Phone', blank=True) # Field name made lowercase.
    eventhighlight = models.CharField(max_length=150, db_column='EventHighlight', blank=True) # Field name made lowercase.
    eventorganizer = models.CharField(max_length=150, db_column='EventOrganizer', blank=True) # Field name made lowercase.

    class Meta:
        db_table = u'scraped_events_vw'

class Event(models.Model):
    """Event model"""
    xid = models.CharField(_('external id'), max_length=200, blank=True)
    title = models.CharField(max_length=200)
    slug = models.SlugField()
    place = models.ForeignKey(Place, blank=True, null=True)
    one_off_place = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    submitted_by = models.ForeignKey(User, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    categories = models.ManyToManyField(Category, verbose_name=_('event categories'), blank=True)

    class Meta:
        verbose_name = _('event')
        verbose_name_plural = _('events')

    def __unicode__(self):
        return self.title


class EventTime(models.Model):
    """EventTime model"""
    event = models.ForeignKey(Event, related_name='event_times')
    start = models.DateTimeField()
    end = models.DateTimeField(blank=True, null=True)
    is_all_day = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('event time')
        verbose_name_plural = _('event times')

    @property
    def is_past(self):
        NOW = datetime.date.now()
        if self.start < NOW:
            return True
        return False

    def __unicode__(self):
        return u'%s' % self.event.title

    @permalink
    def get_absolute_url(self):
        return ('event_detail', None, {
            'year': self.start.year,
            'month': self.start.strftime('%b').lower(),
            'day': self.start.day,
            'slug': self.event.slug,
            'event_id': self.event.id
        })
