import os
import datetime
from collections import defaultdict
from binascii import hexlify

from django.db import models, connection
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from sorl.thumbnail import ImageField
from places.models import Place
import events.config
from livesettings import config_value

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
    icon = ImageField(upload_to='category_icons', blank=True, null=True) # FIXME deprecated remove
    image = ImageField(upload_to='category_images', blank=True, null=True)
    thumb = ImageField(upload_to='category_thumbs', blank=True, null=True) # FIXME deprecated remove
    button_icon = ImageField(upload_to='category_button_icons', blank=True, null=True)
    small_icon = ImageField(upload_to='category_small_icons', blank=True, null=True)
    color = models.CharField(max_length=7, blank=True)

    objects = CategoryManager()
    concrete = CategoryConcreteManager()
    abstract = CategoryAbstractManager()

    @property
    def icon_path(self):
        return os.path.split(self.icon.name)[-1] if self.icon else None

    @property
    def thumb_path(self):
        return self.icon and os.path.split(self.thumb.name)[-1] or ''

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
        # This could be setting
        future_instance = datetime.timedelta(days=61) + instant
        return self.distinct().filter(occurrences__start_date__gte=instant).\
               filter(occurrences__start_date__lte=future_instance)

    def filter_user_actions(self, user, actions='GX'):
        # FIXME hackish
        exclusions = user.event_actions.filter(event__in=self, action__in=actions) \
            .values_list('event_id', flat=True)
        return self.exclude(id__in=exclusions)

    def featured(self):
        featured_event_id = config_value('EVENTS', 'FEATURED_EVENT_ID')
        return self.filter(id=featured_event_id)

class EventQuerySet(models.query.QuerySet, EventMixin):
    pass

class EventManager(models.Manager, EventMixin):
    def get_query_set(self):
        return EventQuerySet(self.model)

    def make_random_secret_key(self):
        return hexlify(os.urandom(5))

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
    popularity_score = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    secret_key = models.CharField(blank=True, max_length=10)

    objects = EventManager()
    active = EventActiveManager()

    class Meta:
        verbose_name_plural = _('events')

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
            .only('place__image').exclude(place__image__isnull=True).exclude(place__image__iexact='')[:1])
        if occurrences_with_place_image:
            return occurrences_with_place_image[0].place.image

        concrete_category = ctree.get(id=self.concrete_category_id)
        if concrete_category.icon:
            return concrete_category.icon

        concrete_parent_category = ctree.surface_parent(concrete_category)
        if concrete_parent_category and concrete_parent_category.icon:
            return concrete_parent_category.icon

    @property
    def best_image(self):
        if self.image:
            return self.image

        occurrences_with_place_image = list(self.occurrences.select_related('place') \
            .only('place__image').exclude(place__image__isnull=True).exclude(place__image__iexact='')[:1])
        if occurrences_with_place_image:
            return occurrences_with_place_image[0].place.image

        if self.concrete_category.image:
            return self.concrete_category.image

        concrete_parent_category = self.summary.concrete_parent_category
        if concrete_parent_category and concrete_parent_category.image:
            return concrete_parent_category.image

    @property
    def date_range(self):
        """Min and max of event dates and distinct count"""
        # FIXME refactor into SQL aggregation
        dates = self.occurrences.values_list('start_date', flat=True) \
            .distinct()
        if dates:
            return min(dates), max(dates), len(dates)
        else:
            return None, None, 0

    @property
    def time_range(self):
        """Min and max of event times and distinct count"""
        # FIXME refactor into SQL aggregation
        # FIXME naive in assumption of at least one start_time
        times = self.occurrences.values_list('start_time', flat=True) \
            .filter(start_time__isnull=False).distinct()
        if times:
            return min(times), max(times), len(times)
        else:
            return None, None, 0

    @property
    def price_range(self):
        """Min and max of event prices"""
        # FIXME refactor into SQL aggregation
        # FIXME circular import is bothersome
        # FIXME naive in regards to units
        from prices.models import Price
        prices = Price.objects.filter(occurrence__in=self.occurrences.all()) \
            .values_list('quantity', flat=True).distinct()
        if prices:
            return min(prices), max(prices), len(prices)

    @property
    def place(self):
        """Title and address of the most common place and distinct count"""
        from places.models import Place
        place_counts = self.occurrences.values('place') \
            .annotate(place_count=models.Count('place')).order_by('-place_count')
        place_id = place_counts[0]['place']
        place = Place.objects.select_related('point__city').get(id=place_id)
        return place.title, place.address, len(place_counts)

    @property
    def places(self):
        """
        All places for this event
        """
        # Optimization FIXME: optimize this with a single query.
        place_ids = self.occurrences.values('place')
        places = Place.objects.filter(id__in=place_ids)
        return places


    def __unicode__(self):
        return self.title

class EventSummaryManager(models.Manager):
    def for_event(self, event, ctree, commit=True):
        """
        Arguments:
            'event':  Event to be summarized.
            'commit': A flag that saves the self summary if set. Mostly for debugging.
        Summarize a single self for the UI.
        Why: Performance. This ensure when a user makes a request, we don't need
        to perform any joins and can return information from a single table.
        """
        occurrence_count = event.occurrences.count()
        if not occurrence_count:
            raise Exception('Event has no occurrences.')

        summary = self.model()
        summary.event = event
        summary.title = event.title
        summary.occurrence_count = occurrence_count

        summary.concrete_category_id = event.concrete_category_id
        summary.concrete_parent_category_id = ctree \
            .surface_parent(ctree.get(id=event.concrete_category_id)).id

        summary.start_date_earliest, summary.start_date_latest, \
            summary.start_date_distinct_count = event.date_range

        summary.start_time_earliest, summary.start_time_latest, \
            summary.start_time_distinct_count = event.time_range

        summary.place_title, summary.place_address, \
            summary.place_distinct_count = event.place

        price_range = event.price_range
        if price_range:
            summary.price_quantity_min, summary.price_quantity_max, _ = price_range

        if commit:
            summary.save()
        return summary

class EventSummary(models.Model):
    """Everything is a text, string or URL (for front end use)"""
    event = models.OneToOneField(Event, related_name='summary', primary_key=True)
    title = models.CharField(max_length=200)
    concrete_category = models.ForeignKey(Category, related_name='event_summaries')
    concrete_parent_category = models.ForeignKey(Category)
    occurrence_count = models.IntegerField()
    start_date_earliest = models.DateField()
    start_date_latest = models.DateField(blank=True, null=True)
    start_date_distinct_count = models.IntegerField()
    start_time_earliest = models.TimeField(blank=True, null=True)
    start_time_latest = models.TimeField(blank=True, null=True)
    start_time_distinct_count = models.IntegerField()
    price_quantity_min = models.FloatField(null=True)
    price_quantity_max = models.FloatField(null=True)
    place_title = models.CharField(max_length=255, blank=True)
    place_address = models.CharField(max_length=200, blank=True)
    place_distinct_count = models.IntegerField()

    objects = EventSummaryManager()

class OccurrenceMixin(object):
    def future(self):
        return self.filter(start_date__gte=datetime.date.today())

class OccurrenceQuerySet(models.query.QuerySet, OccurrenceMixin):
    pass

class OccurrenceManager(models.Manager, OccurrenceMixin):
    def get_query_set(self):
        return OccurrenceQuerySet(self.model)

class Occurrence(models.Model):
    """Models a particular occurrence of an event"""
    from places.models import Place
    event = models.ForeignKey(Event, related_name='occurrences')
    place = models.ForeignKey(Place, related_name='occurrences')
    one_off_place = models.CharField(max_length=200, blank=True)
    start_date = models.DateField()
    start_time = models.TimeField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    is_all_day = models.BooleanField(default=False)

    objects = OccurrenceManager()

    class Meta:
        verbose_name_plural = _('occurrences')

    @property
    def is_past(self): pass

    @property
    def is_future(self): pass

    @property
    def is_now(self): pass

# ==========
# = Source =
# ==========
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
    """By convention, the source and spider name(s) will be correlated"""
    name = models.CharField(max_length=50, unique=True)
    domain = models.CharField(max_length=100)
    default_concrete_category = models.ForeignKey(Category,
        related_name='sources_with_default_concrete'
    )
    default_abstract_categories = models.ManyToManyField(Category,
        related_name='sources_with_default_abstract'
    )

    objects = SourceManager()

    def __unicode__(self):
        return self.name
