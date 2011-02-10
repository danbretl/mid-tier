import datetime, random

from django.template.defaultfilters import slugify

from places.models import Place
from events.models import Event, Occurrence, User
from events.utils import CachedCategoryTree
from behavior.models import Category

class MockInitializer(object):
    def __init__(self, n_events_per_concrete_category=100):
        self.n_events_per_concrete_category = n_events_per_concrete_category

    def run(self):
        ctree = CachedCategoryTree()

        tester_api = User.objects.get(username='tester_api')
        village_vanguard = Place.objects.get(slug='village-vanguard')

        description = """My apartment is infested with koala bears. It's the cutest infestation ever. Way better than cockroaches. When I turn on the light, a bunch of koala bears scatter, but I don't want them too. I'm like, "Hey... Hold on fellows... Let me hold one of you, and feed you a leaf." Koala bears are so cute, why do they have to be so far away from me. We need to ship a few over, so I can hold one, and pat it on its head."""

        for concrete_category in ctree.concretes:
            for n_events in xrange(self.n_events_per_concrete_category):
                # create an event
                title = '%s event #%i' % (concrete_category.title, n_events)
                e = Event(
                    xid = 'xid-%i' % n_events,
                    title = title,
                    slug = slugify(title),
                    description = description,
                    submitted_by = tester_api,
                    url = 'http://abextratech.com/',
                    image_url = 'http://www3.pictures.fp.zimbio.com/Vicky+Cristina+Barcelona+Movie+Stills+-Zma0rlbU7Tl.jpg',
                    video_url = 'http://www.youtube.com/watch?v=a1Y73sPHKxw'
                )
                e.concrete_category = concrete_category
                e.save()

                # add some abstract categories to it
                for ac in random.sample(ctree.abstracts, random.randint(1,5)):
                    e.categories.add(ac)

                # add some occurrences
                for n_occurences in xrange(random.randint(1,5)):
                    today = datetime.date.today()
                    Occurrence(
                        event = e,
                        place = village_vanguard if n_occurences % 2 else None,
                        one_off_place = "" if n_occurences % 2 else "AbextraTech @ 93 Leonard St., New York, NY 10013",
                        start_date = today,
                        start_time = datetime.datetime.now().time(),
                        end_date = today,
                        end_time = datetime.datetime.now().time(),
                        is_all_day = False
                    ).save()


class PreprocessRouter(object):
    """A router to control all database operations on models in
    the `preprocess` application to the `scrape` db"""
    
    app_name = 'preprocess'
    db_name = 'scrape'

    def db_for_read(self, model, **hints):
        "Point all operations on `preprocess` models to `scrape`"
        if model._meta.app_label == self.app_name:
            return self.db_name
        return None

    def db_for_write(self, model, **hints):
        "Point all operations on `preprocess` models to `scrape`"
        if model._meta.app_label == self.app_name:
            return self.db_name
        return None

    def allow_relation(self, obj1, obj2, **hints):
        "Allow any relation if a model in `preprocess` is involved"
        if obj1._meta.app_label == self.app_name or obj2._meta.app_label == self.app_name:
            return True
        return None

    def allow_syncdb(self, db, model):
        "Make sure the `preprocess` app only appears on the `scrape` db"
        if db == self.db_name:
            return model._meta.app_label == self.app_name
        elif model._meta.app_label == self.app_name:
            return False
        return None