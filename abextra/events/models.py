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
    association_coefficient = models.FloatField(default=0)

    class Meta:
        verbose_name_plural = _('categories')

    def __unicode__(self):
        return u'%s' % self.title

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
    url = models.URLField(verify_exists=False, max_length=300)
    image_url = models.URLField(verify_exists=False, max_length=300, blank=True)
    video_url = models.URLField(verify_exists=False, max_length=200, blank=True)
    categories = models.ManyToManyField(Category, verbose_name=_('event categories'), blank=True)

    @property
    def cat_titles(self):
        return ', '.join(e.title for e in self.categories.all())

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

from places.models import Place, Point, City
import datetime, re
rg=re.compile(r'[a-z]*')
class ScrapedEvent(models.Model):
    """Works with the sraped events view"""
    internalid = models.IntegerField(db_column='InternalID', primary_key=True) 
    title = models.CharField(max_length=600, db_column='Title', blank=True) 
    externalid = models.CharField(max_length=90, db_column='ExternalID', blank=True) 
    eventdate = models.DateField(null=True, db_column='EventDate', blank=True) 
    starttime = models.TextField(db_column='StartTime') # This field type is a guess.
    endtime = models.TextField(db_column='EndTime') # This field type is a guess.
    description = models.CharField(max_length=9000, db_column='Description', blank=True) 
    url = models.CharField(max_length=600, db_column='URL', blank=True) 
    imageurl = models.CharField(max_length=600, db_column='ImageURL', blank=True) 
    videourl = models.CharField(max_length=600, db_column='VideoURL', blank=True) 
    location = models.CharField(max_length=600, db_column='Location', blank=True) 
    email = models.CharField(max_length=150, db_column='Email', blank=True) 
    phone = models.CharField(max_length=45, db_column='Phone', blank=True) 
    eventhighlight = models.CharField(max_length=150, db_column='EventHighlight', blank=True) 
    eventorganizer = models.CharField(max_length=150, db_column='EventOrganizer', blank=True) 
    cost = models.IntegerField(null=True, db_column='Cost', blank=True) 
    last_modified = models.DateTimeField(db_column='Last_Modified')

    class Meta:
        db_table = u'scraped_events_vw'
        managed = False

    def __unicode__(self):
        return u'%s' % self.title

    def slugify(self):
        return '-'.join(p for p in rg.findall(self.title.lower()) if p)[:50]

    def to_event(self, save=True):
        e = Event()
        e.xid = self.internalid
        e.title = self.title
        e.slug = self.slugify()
        e.one_off_place = self.location or ''
        e.description = self.description or ''
        # e.submitted_by = models.ForeignKey(User, blank=True, null=True)
        e.url = self.url or 'http://abextratech.com/eventure/'
        e.image_url = self.imageurl or ''
        e.video_url = self.videourl or ''
        if save: e.save()

        if self.eventdate:
            et = EventTime()
            et.event = e
            et.start = datetime.datetime.combine(self.eventdate, self.starttime)
            et.end = datetime.datetime.combine(self.eventdate, self.endtime)
            if save: et.save()

        return e