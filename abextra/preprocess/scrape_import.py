from collections import defaultdict
from django.template.defaultfilters import slugify

from preprocess import models_external as x_models
from preprocess.models import ExternalCategory
from events.models import Event, Occurrence
from places.models import Place, Point, City
from prices.models import Price
from events.utils import CachedCategoryTree

class ImportScrapeData(object):

    def __init__(self):
        self.x_event_categories = defaultdict(lambda: [])
        self.places_by_xid = {}
        self.occurrences_by_xid = {}
        self.prices_by_xid = {}
        self.events_by_xid = {}
        self.x_categories_by_xid = {}
        self.ctree = CachedCategoryTree()

    def run(self):
        for x_category in x_models.Category.objects.all():
            self.x_categories_by_xid[x_category.id] = x_category

        for x_event_category in x_models.EventCategory.objects.all():
            self.add_event_category(x_event_category)

        for x_loc in x_models.Location.objects.all():
            self.add_place(x_loc)

        for x_event in x_models.Event.objects.all():
            self.add_event(x_event)

        for x_occurrence in x_models.Occurrence.objects.all():
            self.add_occurrence(x_occurrence)

        for x_price in x_models.Price.objects.all():
            self.add_price(x_price)

    def add_price(self, x_price):
        occurrence = self.occurrences_by_xid.get(x_price.occurrence_id)
        if occurrence:
            price, created = Price.objects.get_or_create(
                quantity=x_price.quantity,
                units=x_price.units,
                remark=x_price.remark or '',
                occurrence=occurrence
            )
            self.prices_by_xid[x_price.id] = price

    def add_occurrence(self, x_occurrence):
        event = self.events_by_xid.get(x_occurrence.event_id)
        if event:
            place = self.places_by_xid[x_occurrence.location_id]

            occurrence, created = Occurrence.objects.get_or_create(
                event=event,
                place=place,
                # one_off_place= models.CharField(max_length=200, blank=True),
                start_date=x_occurrence.start_date,
                start_time=x_occurrence.start_time,
                end_date= x_occurrence.end_date,
                end_time= x_occurrence.end_time,
                # is_all_day= models.BooleanField(default=False)
            )
            self.occurrences_by_xid[x_occurrence.id] = occurrence

    def add_event(self, x_event):
        x_categories = self.x_event_categories.get(x_event.id) # TODO will be lost
        if x_categories:
            x_category_xids = map(lambda x_category: x_category.xid, x_categories)
            category_ids = ExternalCategory.objects \
                .values_list('category_id', flat=True) \
                .filter(xid__in=x_category_xids)

            concrete_category = self.ctree.deepest_category(
                self.ctree.get(id=category_id) for category_id in category_ids
            )

            event, created = Event.objects.get_or_create(
                xid=x_event.guid,
                title=x_event.title,
                slug=slugify(x_event.title)[:50],
                description=x_event.description or '',
                # submitted_by = models.ForeignKey(User, blank=True, null=True)
                # created = models.DateTimeField(auto_now_add=True)
                # modified = models.DateTimeField(auto_now=True)
                url=x_event.url or '',
                image_url=x_event.image_url or '',
                # video_url = models.URLField(verify_exists=False, max_length=200, blank=True)
                concrete_category=concrete_category,
                # categories = models.ManyToManyField(Category, related_name='events_abstract', verbose_name=_('abstract categories'))
            )
            self.events_by_xid[x_event.id] = event

    def add_place(self, x_location):
        city, created = City.objects.get_or_create(
            city=x_location.city,
            state=x_location.state,
            slug=slugify(u'-'.join((x_location.city, x_location.state)))
        )
        point, created = Point.objects.get_or_create(
            latitude=x_location.latitude,
            longitude=x_location.longitude,
            address=x_location.address,
            city=city,
            zip=x_location.zipcode,
            country='US'
        )
        place, created = Place.objects.get_or_create(
            point=point,
            # prefix = '',
            title=x_location.title,
            slug=slugify(x_location.title)[:50],
            # nickname=models.CharField(_('nickname'), blank=True, max_length=100),
            # unit=models.CharField(_('unit'), blank=True, max_length=100, help_text='Suite or Apartment #'),
            phone=x_location.phone if x_location.phone and (not ':' in x_location.phone) else None or '',
            url=x_location.url or x_location.guid, # FIXME source (villagevoice) specific
            image_url=x_location.image_url or ''
            # email=models.EmailField(_('email'), blank=True),
            # description = models.TextField(_('description'), blank=True),
            # status = models.IntegerField(_('status'), choices=STATUS_CHOICES, default=1)
            # created = models.DateTimeField(auto_now_add=True)
            # modified = models.DateTimeField(auto_now=True)
            # place_types = models.ManyToManyField(PlaceType, blank=True)
        )
        self.places_by_xid[x_location.id] = place

    def add_event_category(self, x_event_category):
        x_category = self.x_categories_by_xid[x_event_category.category_id]
        self.x_event_categories[x_event_category.event_id].append(x_category)
