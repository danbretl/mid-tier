import os
import datetime
from collections import defaultdict

from django.db import models, connection
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from sorl.thumbnail import ImageField

from places.models import Place

# ============
# = Category =
# ============
class CategoryManager(models.Manager):
    def for_events(self, event_ids, category_types='CA'):
        if not event_ids:
            return {}
        select_by_type = {
            'a': 'SELECT event_id, category_id FROM events_event_categories WHERE event_id IN %(event_ids)s',
            'c': 'SELECT id, concrete_category_id FROM events_event WHERE id IN %(event_ids)s'
        }
        selects = map(select_by_type.get, category_types.lower())
        cursor = connection.cursor()
        single_item_hack = event_ids if len(event_ids) > 1 else event_ids * 2
        cursor.execute(' UNION '.join(selects), {'event_ids': single_item_hack})
        category_ids_by_event_id = defaultdict(lambda: [])
        for event_id, category_id in cursor.fetchall():
            category_ids_by_event_id[event_id].append(category_id)
        return category_ids_by_event_id

class CategoryConcreteManager(models.Manager):
    def get_query_set(self):
           return super(CategoryConcreteManager, self).get_query_set() \
               .filter(category_type__exact='C')

class CategoryAbstractManager(models.Manager):
    def get_query_set(self):
           return super(CategoryAbstractManager, self).get_query_set() \
               .filter(category_type__exact='A')

class Category(models.Model):
    """Category model"""
    TYPE_CHOICES = ( ('C', 'Concrete'), ('A', 'Abstract'), ('O', 'Other') )
    category_type = models.CharField(max_length=1, choices=TYPE_CHOICES)
    title = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey('self', related_name='subcategories', blank=True, null=True)
    is_associative = models.BooleanField(default=True)
    association_coefficient = models.FloatField(default=0)
    # TODO bring this out into a OneToOne CategoryGraphics class
    icon = ImageField(upload_to='category_icons', blank=True, null=True)
    color = models.CharField(max_length=7, blank=True)

    objects = CategoryManager()
    concrete = CategoryConcreteManager()
    abstract = CategoryAbstractManager()

    @property
    def icon_path(self):
        return os.path.split(self.icon.name)[-1] if self.icon else None

    def parent_title(self):
        return self.parent.title
    parent_title.admin_order_field = 'parent__title'

    class Meta:
        verbose_name_plural = _('categories')

    def __unicode__(self):
        return self.title

# =========
# = Event =
# =========
class EventMixin(object):
    """
    see http://www.cupcakewithsprinkles.com/django-custom-model-manager-chaining/
    """
    def future(self):
        instant = datetime.date.today()
        return self.distinct().filter(occurrences__start_date__gte=instant)

    def filter_user_actions(self, user, actions='GVI'):
        user_q = models.Q(actions__user=user)
        actions_q = models.Q(actions__action__in=actions)
        q = (user_q & actions_q) | models.Q(actions__isnull=True)
        return self.filter(q)

class EventQuerySet(models.query.QuerySet, EventMixin):
    pass

class EventManager(models.Manager, EventMixin):
    def get_query_set(self):
        return EventQuerySet(self.model)

class EventActiveManager(EventManager):
    def get_query_set(self):
        return super(EventActiveManager, self).get_query_set().filter(is_active=True)

class Event(models.Model):
    """Event model"""
    xid = models.CharField(_('external id'), max_length=200, blank=True)
    title = models.CharField(max_length=200)
    slug = models.SlugField()
    description = models.TextField(blank=True)
    submitted_by = models.ForeignKey(User, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    url = models.URLField(verify_exists=False, max_length=300)
    image = ImageField(upload_to='event_images', blank=True, null=True)
    image_url = models.URLField(verify_exists=False, max_length=300, blank=True)
    video_url = models.URLField(verify_exists=False, max_length=200, blank=True)
    concrete_category = models.ForeignKey(Category, related_name='events_concrete')
    categories = models.ManyToManyField(Category, related_name='events_abstract', verbose_name=_('abstract categories'))
    is_active = models.BooleanField(default=True)

    objects = EventManager()
    active = EventActiveManager()

    def _concrete_category(self):
        """Used only by the admin site"""
        return self.concrete_category.title
    _concrete_category.admin_order_field = 'concrete_category__title'

    def _abstract_categories(self):
        """Used only by the admin site"""
        return ', '.join(self.categories.values_list('title', flat=True))

    # FIXME hacked up api
    def image_chain(self, ctree):
        if self.image:
            return self.image

        occurrences_with_place_image = list(self.occurrences.select_related('place') \
            .only('place__image').filter(place__image__isnull=False)[:1])
        if occurrences_with_place_image:
            return occurrences_with_place_image[0].place.image

        concrete_category = ctree.get(id=self.concrete_category_id)
        if concrete_category.icon:
            return concrete_category.icon

        concrete_parent_category = ctree.surface_parent(concrete_category)
        if concrete_parent_category and concrete_parent_category.icon:
            return concrete_parent_category.icon

    class Meta:
        verbose_name_plural = _('events')

class Occurrence(models.Model):
    """Models a particular occurrence of an event"""
    event = models.ForeignKey(Event, related_name='occurrences')
    place = models.ForeignKey(Place, related_name='occurrences')
    one_off_place = models.CharField(max_length=200, blank=True)
    start_date = models.DateField()
    start_time = models.TimeField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    is_all_day = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = _('occurrences')

    @property
    def is_past(self): pass

    @property
    def is_future(self): pass

    @property
    def is_now(self): pass


class EventSummary(models.Model):
    """
    To do.
    Everything is a text, string or URL (for front end use)
    """
    id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    url = models.URLField(verify_exists=False, max_length=300)
    concrete_category = models.CharField(max_length=50)
    date_range = models.CharField(max_length=25)
    price_range = models.CharField(max_length=25)
    time = models.CharField(max_length=25)
    place = models.CharField(max_length=200, blank=True)


    # Crashes with unicode encoder errors in some cases.
    """
    def __repr__(self):
        str_obj =  "\nTitle      : " + self.title
        str_obj += "\nDescription: " + self.description
        str_obj += "\nDate Range : " + self.date_range
        str_obj += "\nTime       : " + self.time
        str_obj += "\nPrice Range: " + self.price_range
        str_obj += "\nPlace      : " + self.place
        str_obj += "\nURL        : " + self.url
        return str_obj
    """ 

    
    
    
