from django.db import models
from django.utils.translation import ugettext_lazy as _
from events.models import Source, Category

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
        unique_together = (('source', 'xid'),)


class RegexCategory(models.Model):
    """
    Maps external categories to internal categories by checking with a regular
    expression string.
    """
    source = models.ForeignKey(Source, related_name='source_regex_categories')
    regex = models.CharField(max_length=100)
    model_type = models.CharField(max_length=50, blank=True, null=True)
    category = models.ForeignKey(Category,
                                 related_name='source_regex_categories',
                                 blank=True, null=True)
