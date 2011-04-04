import os
import datetime
from collections import defaultdict

from django.db import models, connection
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from sorl.thumbnail import ImageField
#from events.utils import CachedCategoryTree
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


class EventSummary(models.Model):
    """
    To do.
    Everything is a text, string or URL (for front end use)
    """
    title = models.CharField(max_length=200)
    concrete_category = models.ForeignKey(Category, related_name='event_summary_concrete')
    date_range = models.CharField(max_length=25, blank=True)
    price_range = models.CharField(max_length=25, blank=True, null=False)
    time = models.CharField(max_length=25, blank=True)
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
    summary = models.OneToOneField(EventSummary, null=True)

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


    def summarize_event(self, ctree=None, commit=False):
        """
        Arguments:
            'self' :  A django event object.
            'commit': A flag that saves the self summary if set. Mostly for debugging.
        Summarize a single self for the UI.
        Why: Performance. This ensure when a user makes a request, we don't need
        to perform any joins and can return information from a single table.
        When: This is performed after a scrape and before the information gets
        stored on the self database.
        """
        if not ctree:
            ctree = CachedCategoryTree()

        e_s = EventSummary()
        # This is interesting: http://djangosnippets.org/snippets/1258/
        #related_objs = CollectedObjects()
        #self._collect_sub_objects(related_objs)
        #Event.objects.select_related()
        e_s.concrete_category = ctree.surface_parent(self.concrete_category)
        e_s.title = self.title
        e_s.url = self.url
        e_s.description = self.description

        # ToDo: We could potentially filter out any events here that do not have
        # future occurrences. Since we are using this for scrape, the
        # expectations is that past events don't get scraped. 

        #Get occurrence related information. 
        occurrence_objs = self.occurrences.all()
        # If there are no occurrence objects, then the self hasn't been
        # scheduled for a date, time and place. Forget this self. 
        if not occurrence_objs:
            return
        dates = [o_obj.start_date for o_obj in occurrence_objs]
        date_range = [min(dates), max(dates)]
        e_s.date_range = ' - '.join([dt.strftime('%x') for dt in date_range])
        occ_obj = None 

        try:
            # min could potentially be run on an empty list (since invalid times get
            # filtered out)
            time, occ_obj = min([(o_obj.start_time, o_obj)
                                 for o_obj in occurrence_objs if o_obj.start_time])
            e_s.time = time.strftime('%X')
        except:
            #e_s.time = None
            occ_obj = occurrence_objs[0]

        try:
            e_s.place = occ_obj.place.full_title + ',' + occ_obj.place.address
        except:
            # This also imples a bad scrape. We have an occurrence
            # without a place/location.
            pass

        price_objs = [price.quantity for price in occ_obj.prices.all()]
        try:
            #min could potentially be run on an empty list of price objs. 
            e_s.price_range = str(min(price_objs)) + ' - ' + str(max(price_objs))
        except:
            pass

        if commit:
            # Here we can also check if the event_summary already exists and
            # update relevant informat
            e_s.id = self.id
            self.summary = e_s 
            e_s.save()
            self.save()
            #self.save()

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



    
    
    
