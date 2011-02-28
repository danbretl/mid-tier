from django.db import models

class ExternalScrapeManager(models.Manager):
    def get_query_set(self):
           return super(ExternalScrapeManager, self).get_query_set() \
               .using('scrape')

class ExternalScrapeModel(models.Model):
    objects = ExternalScrapeManager()
    class Meta:
        abstract = True


# -- inspectdb models + tweaks  :: should inherit from ExternalScrapeModel

class Category(ExternalScrapeModel):
    id = models.IntegerField(primary_key=True)
    xid = models.IntegerField(null=True, blank=True)
    source = models.CharField(max_length=900, blank=True)
    name = models.CharField(max_length=300, blank=True)
    class Meta:
        db_table = u'category'
        managed = False

class Event(ExternalScrapeModel):
    id = models.IntegerField(primary_key=True)
    guid = models.CharField(unique=True, max_length=900, blank=True)
    title = models.CharField(max_length=1800, blank=True)
    description = models.TextField(blank=True)
    url = models.CharField(max_length=1800, blank=True)
    image_url = models.CharField(max_length=900, blank=True)
    image_path = models.CharField(max_length=300, blank=True)
    video_url = models.CharField(max_length=900, blank=True)
    source = models.CharField(max_length=300, blank=True)
    class Meta:
        db_table = u'event'
        managed = False

class EventCategory(ExternalScrapeModel):
    event_id = models.IntegerField(null=True, blank=True)
    category_id = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = u'event_category'
        managed = False

class Location(ExternalScrapeModel):
    id = models.IntegerField(primary_key=True)
    guid = models.CharField(unique=True, max_length=900, blank=True)
    title = models.CharField(max_length=900, blank=True)
    address = models.CharField(max_length=600, blank=True)
    city = models.CharField(max_length=300, blank=True)
    state = models.CharField(max_length=300, blank=True)
    zipcode = models.CharField(max_length=300, blank=True)
    url = models.CharField(max_length=900, blank=True)
    phone = models.CharField(max_length=150, blank=True)
    latitude = models.CharField(max_length=60, blank=True)
    longitude = models.CharField(max_length=60, blank=True)
    source = models.CharField(max_length=300, blank=True)
    image_url = models.CharField(max_length=900, blank=True)
    image_path = models.CharField(max_length=300, blank=True)
    class Meta:
        db_table = u'location'
        managed = False

class Occurrence(ExternalScrapeModel):
    id = models.IntegerField(primary_key=True)
    guid = models.CharField(unique=True, max_length=900, blank=True)
    event_id = models.IntegerField(null=True, blank=True)
    timestamp = models.DateTimeField()
    start_date = models.DateField()
    start_time = models.TextField(blank=True) # This field type is a guess.
    end_date = models.DateField(null=True, blank=True)
    end_time = models.TextField(blank=True) # This field type is a guess.
    one_off_location = models.CharField(max_length=1800, blank=True)
    location_id = models.IntegerField(null=True, blank=True)
    is_soldout = models.IntegerField()
    class Meta:
        db_table = u'occurrence'
        managed = False

class Price(ExternalScrapeModel):
    id = models.IntegerField(primary_key=True)
    quantity = models.FloatField(null=True, blank=True)
    units = models.CharField(max_length=300, blank=True)
    remark = models.CharField(max_length=300, blank=True)
    occurrence_id = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = u'price'
        managed = False


        # def to_event(self, save=True):
        #     e = Event()
        #     e.xid = self.internalid
        #     e.title = self.title
        #     e.slug = self.slug
        #     e.one_off_place = self.location or ''
        #     e.description = self.description or ''
        #     # e.submitted_by = models.ForeignKey(User, blank=True, null=True)
        #     e.url = self.url or 'http://abextratech.com/eventure/'
        #     e.image_url = self.imageurl or ''
        #     e.video_url = self.videourl or ''
        #     if save: e.save()
        # 
        #     # if self.eventdate:
        #     #     et = EventTime()
        #     #     et.event = e
        #     #     et.start = datetime.datetime.combine(self.eventdate, self.starttime)
        #     #     et.end = datetime.datetime.combine(self.eventdate, self.endtime)
        #     #     if save: et.save()
        # 
        #     return e