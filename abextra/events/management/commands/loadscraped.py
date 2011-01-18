from django.core.management.base import NoArgsCommand
from abextra.events.models import ScrapedEvent

class Command(NoArgsCommand):
    help = 'Loads scraped events from the scraped view'

    def handle(self, **options):
        try:
            for e in ScrapedEvent.objects.all(): e.to_event()
        except e:
            raise CommandError(e)
        self.stdout.write('Successfully loaded scraped events')