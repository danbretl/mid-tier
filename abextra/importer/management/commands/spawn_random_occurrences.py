from django.core.management.base import BaseCommand
from optparse import make_option
from events.models import Event
from places.models import Place
import datetime

class Command(BaseCommand):
    help = '''Given an event ID, spawn random occurrences for it
    on the same day but at different times and places'''
    option_list = BaseCommand.option_list + (
        make_option('--n',
                    action='store',
                    dest='n',
                    default='int',
                    help='Number of occurrences to spawn'),
        make_option('--id',
                    action='store',
                    dest='id',
                    type='int',
                    help='ID of target event'))

    def handle(self, **options):
        if not options:
            self.stdout.write('No options selected. Try --help for usage.')

        n_occs = options.get('n')
        if not n_occs:
            self.stdout.write('Invalid number of occurrences to create\n')
            return
        n_occs = int(n_occs)

        event_id = options.get('id')
        events = Event.objects.filter(id=event_id)
        if not events:
            self.stdout.write('Event not found\n')
            return
        event = events[0]

        places = Place.objects.all()[:n_occs]
        if Place.objects.count() < n_occs:
            self.stdout.write("There aren't that many places in the database!\n")
            return

        existing_occurrence = event.occurrences.all()[0]
        for ix in range(n_occs):
            existing_occurrence.id = None
            existing_occurrence.place = places[ix]
            existing_occurrence.save()
            self.stdout.write('Created occurence: %s\n' % occ)
