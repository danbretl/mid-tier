from django.core.management.base import BaseCommand
from optparse import make_option
from events.models import Event
from places.models import Place
from itertools import cycle

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

        place_count = Place.objects.count()
        if place_count < n_occs:
            self.stdout.write('Will cycle on %i places.' % place_count)
        places = cycle(Place.objects.values_list('id', flat=True))

        future_occurrences = event.occurrences.future()
        if not future_occurrences:
            self.stdout.write('Event has no future occurrences.')
            return
        existing_occurrence = future_occurrences[0]
        for ix in range(n_occs):
            existing_occurrence.id = None
            existing_occurrence.place_id = places.next()
            existing_occurrence.save()
        self.stdout.write('Created occurrences')
