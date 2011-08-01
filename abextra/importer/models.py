from django.db import models
from django.utils.translation import ugettext_lazy as _
from events.models import Source, Category, Event

class ExternalCategory(models.Model):
    xid = models.CharField(max_length=300)
    name = models.CharField(max_length=100)
    source = models.ForeignKey(Source)
    concrete_category = models.ForeignKey(Category, related_name='externalcategory_concrete_set', blank=True, null=True)
    abstract_categories = models.ManyToManyField(Category, blank=True, null=True)

    def category_title(self):
        return self.category.title
    category_title.admin_order_field = 'category__title'

    class Meta:
        verbose_name_plural = _('external categories')

    def __unicode__(self):
        return self.name


class RegexCategory(models.Model):
    """
    Maps external categories to internal categories by checking with a regular
    expression string.
    """
    # FIXME convert to a more explicit m2m relationship
    source = models.ForeignKey(Source, blank=True, null=True)
    regex = models.CharField(max_length=100)
    model_type = models.CharField(max_length=50, blank=True, null=True)
    category = models.ManyToManyField(Category, blank=True, null=True)

class ConditionalCategory(models.Model):
    """
    Once concrete categorization has been performed, we can use context to
    better categorize abstract categories.
    For example a sports event with Pirate can be classified under the
    Pittsburgh Pirates instead of the abstract category Pirates.
    The idea is to use contextual information when available.
    This is a very painful but somewhat necessary hack.
    """
    conditional_concrete_category = models.ForeignKey(Category, related_name='conditional_concrete_category')
    resulting_categories = models.ManyToManyField(Category)
    regex = models.CharField(max_length=100)
