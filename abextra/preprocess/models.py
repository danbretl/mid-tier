from django.db import models

class Events(models.Model):
    id = models.IntegerField(primary_key=True)
    xid = models.CharField(max_length=300, blank=True)
    title = models.CharField(max_length=1800, blank=True)
    description = models.CharField(max_length=27000, blank=True)
    url = models.CharField(max_length=1800, blank=True)
    image_url = models.CharField(max_length=1800, blank=True)
    video_url = models.CharField(max_length=1800, blank=True)
    class Meta:
        db_table = u'events'
        managed = False

class Occurrences(models.Model):
    id = models.IntegerField(primary_key=True)
    event = models.ForeignKey(Events, related_name='occurrences')
    timestamp = models.DateTimeField()
    start_date = models.DateField()
    start_time = models.TimeField(blank=True)
    end_date = models.DateField(null=True, blank=True)
    end_time = models.TimeField(blank=True)
    location = models.CharField(max_length=1800, blank=True)
    class Meta:
        db_table = u'occurrences'
        managed = False

class Costs(models.Model):
    id = models.IntegerField(primary_key=True)
    occurrence = models.ForeignKey(Occurrences, related_name='costs')
    remark = models.CharField(max_length=300, blank=True)
    price = models.CharField(max_length=300, blank=True)
    class Meta:
        db_table = u'costs'
        managed = False

# ---- old scrape db flat schema ----

import datetime, re
from events.models import Event, EventTime
rg=re.compile(r'[a-z]*')
class ScrapedEvent(models.Model):
    """Works with the sraped events view"""
    internalid = models.IntegerField(db_column='InternalID', primary_key=True) 
    title = models.CharField(max_length=600, db_column='Title', blank=True) 
    externalid = models.CharField(max_length=90, db_column='ExternalID', blank=True) 
    eventdate = models.DateField(null=True, db_column='EventDate', blank=True) 
    starttime = models.TimeField(db_column='StartTime')
    endtime = models.TimeField(db_column='EndTime')
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

    @property
    def slug(self):
        return '-'.join(p for p in rg.findall(self.title.lower()) if p)[:50]

    def to_event(self, save=True):
        e = Event()
        e.xid = self.internalid
        e.title = self.title
        e.slug = self.slug
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