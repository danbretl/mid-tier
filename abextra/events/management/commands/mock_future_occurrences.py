import datetime
from random import sample
from django.core.management.base import NoArgsCommand, CommandError
from django.db.models import Count
from events.models import Event, Occurrence, Category
from places.models import Place

class Command(NoArgsCommand):
    help = 'Create a bunch of fake future occurrences.'

    def handle(self, **options):
        try:
            c = Category.objects.get(slug='movies-media')
            events = Event.active.future()\
                    .filter(summary__concrete_parent_category=c)\
                    .annotate(occurrence_count=Count('occurrences'))\
                    .filter(occurrence_count=1)
            time_delta = datetime.timedelta(hours=4)
            date_delta = datetime.timedelta(days=1)
            places = Place.objects.all()[:20]

            for e in events:
                o = e.occurrences.all()[0]
                if o.start_time:
                    dt = datetime.datetime.combine(o.start_date, o.start_time)
                    for i in range(12):
                        o.pk = None
                        dt += time_delta
                        o.start_date, o.start_time = dt.date(), dt.time()
                        o.place = sample(places, 1)[0]
                        # print 'saving datetime instance: %s' % o
                        o.save()
                else:
                    for i in range(10):
                        o.pk = None
                        o.start_date += date_delta
                        o.place = sample(places, 1)[0]
                        # print 'saving date instance: %s' % o
                        o.save()
                e.save()

        except Exception, e:
            raise CommandError(e)
        self.stdout.write('Successfully added mock occurrences\n')
