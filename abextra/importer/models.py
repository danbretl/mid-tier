from django.db import models
from django.utils.translation import ugettext_lazy as _
from events.models import Source, Category, Event

class ExternalCategory(models.Model):
    xid = models.CharField(max_length=300)
    name = models.CharField(max_length=100)
    source = models.ForeignKey(Source, related_name='external_concrete_category')
    concrete_category = models.ForeignKey(Category,
                                          related_name='external_concrete_category',
                                          blank=True, null=True)
    abstract_categories = models.ManyToManyField(Category,
                                                 related_name='external_abstract_categories',
                                                 blank=True, null=True)

    def category_title(self):
        return self.category.title
    category_title.admin_order_field = 'category__title'

    class Meta:
        verbose_name_plural = _('external categories')

    def __str__(self):
        #return self.name + ' (xid: ' + self.xid + ')'
        return self.name


class RegexCategory(models.Model):
    """
    Maps external categories to internal categories by checking with a regular
    expression string.
    """
    source = models.ForeignKey(Source, related_name='source_regex_categories',
                               blank=True, null=True)
    regex = models.CharField(max_length=100)
    model_type = models.CharField(max_length=50, blank=True, null=True)
    category = models.ForeignKey(Category,
                                 related_name='source_regex_categories',
                                 blank=True, null=True)

class ConditionalCategoryModel(models.Model):
    """
    Once concrete categorization has been performed, we can use context to
    better categorize abstract categories.
    For example a sports event with Pirate can be classified under the
    Pittsburgh Pirates instead of the abstract category Pirates.
    The idea is to use contextual information when available.
    This is a very painful but somewhat necessary hack.
    """
    conditional_category = models.ForeignKey(Category,
                                             related_name='conditional_category',
                                             blank=True, null=True, default=None)
    regex = models.CharField(max_length=100)
    category = models.ForeignKey(Category,
                                 related_name='classified_category',
                                 blank=False, null=False)


class EventExternalCats(models.Model):
    """
    Store an incoming events external categories.
    This will be useful for later analysis and testing of pundits performance.
    """
    external_category = models.ForeignKey(ExternalCategory,
                                          related_name='event_external_cat')
    event = models.ForeignKey(Event, related_name='event_external_cat')

    class Meta:
        unique_together = (('external_category', 'event'),)
