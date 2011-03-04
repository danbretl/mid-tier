from django.db import models
from events.models import Occurrence

class Price(models.Model):
    quantity = models.FloatField(null=True, blank=True)
    units = models.CharField(max_length=300, blank=True)
    remark = models.CharField(max_length=300, blank=True)
    occurrence_id = models.IntegerField(null=True, blank=True)
    objects = MGR()
    class Meta:
        db_table = u'price'
        managed = False
