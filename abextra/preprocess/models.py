from django.db import models
from django.utils.translation import ugettext_lazy as _

from events.models import Category

SOURCE_CACHE = {}

class SourceManager(models.Manager):

    def by_name(self, name):
        try:
            source = SOURCE_CACHE[name]
        except KeyError:
            source = self.get(name=name)
            SOURCE_CACHE[name] = source
        return source

    def clear_cache(self):
        global SOURCE_CACHE
        SOURCE_CACHE = {}

    @property
    def villagevoice(self):
        return self.by_name('villagevoice')

    @property
    def eventful(self):
        return self.by_name('eventful')

class Source(models.Model):
    name = models.CharField(max_length=50, unique=True)
    domain = models.CharField(max_length=100)
    objects = SourceManager()

    def __unicode__(self):
        return self.name

class ExternalCategory(models.Model):
    name = models.CharField(max_length=100)
    xid = models.CharField(max_length=300)
    source = models.ForeignKey(Source, related_name='external_categories')
    category = models.ForeignKey(Category, related_name='external_categories', blank=True, null=True)

    def category_title(self):
        return self.category.title
    category_title.admin_order_field = 'category__title'

    class Meta:
        unique_together = (('name', 'source'),)
        verbose_name_plural = _('external categories')
