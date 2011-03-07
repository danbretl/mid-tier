from django.db import models
from events.models import Occurrence

class Price(models.Model):
    quantity = models.DecimalField(max_digits=10, decimal_places=2);
    units = models.CharField(max_length=300, default='dollars')
    remark = models.CharField(max_length=300, blank=True)
    occurrence = models.ForeignKey(related_name='prices')
