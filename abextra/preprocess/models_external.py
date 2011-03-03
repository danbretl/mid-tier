from django.db import models

MGR = lambda: models.Manager().db_manager('scrape')

class Category(models.Model):
    xid = models.IntegerField(null=True, blank=True)
    source = models.CharField(max_length=900, blank=True)
    name = models.CharField(max_length=300, blank=True)
    objects = MGR()
    class Meta:
        db_table = u'category'
        managed = False

class Event(models.Model):
    guid = models.CharField(unique=True, max_length=255, blank=True)
    title = models.CharField(max_length=1800, blank=True)
    description = models.TextField(blank=True)
    url = models.CharField(max_length=1800, blank=True)
    image_url = models.CharField(max_length=900, blank=True)
    image_path = models.CharField(max_length=300, blank=True)
    video_url = models.CharField(max_length=900, blank=True)
    source = models.CharField(max_length=300, blank=True)
    objects = MGR()
    class Meta:
        db_table = u'event'
        managed = False

class EventCategory(models.Model):
    event_id = models.IntegerField(null=True, blank=True, primary_key=True)
    category_id = models.IntegerField(null=True, blank=True)
    objects = MGR()
    class Meta:
        db_table = u'event_category'
        managed = False
        unique_together = (('event_id', 'category_id'),)

class Location(models.Model):
    guid = models.CharField(unique=True, max_length=255, blank=True)
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
    objects = MGR()
    class Meta:
        db_table = u'location'
        managed = False

class Occurrence(models.Model):
    guid = models.CharField(unique=True, max_length=255, blank=True)
    event_id = models.IntegerField(null=True, blank=True)
    timestamp = models.DateTimeField()
    start_date = models.DateField()
    start_time = models.TimeField(blank=True) # This field type is a guess.
    end_date = models.DateField(null=True, blank=True)
    end_time = models.TimeField(blank=True) # This field type is a guess.
    one_off_location = models.CharField(max_length=1800, blank=True)
    location_id = models.IntegerField(null=True, blank=True)
    is_soldout = models.IntegerField()
    objects = MGR()
    class Meta:
        db_table = u'occurrence'
        managed = False

class Price(models.Model):
    quantity = models.FloatField(null=True, blank=True)
    units = models.CharField(max_length=300, blank=True)
    remark = models.CharField(max_length=300, blank=True)
    occurrence_id = models.IntegerField(null=True, blank=True)
    objects = MGR()
    class Meta:
        db_table = u'price'
        managed = False
