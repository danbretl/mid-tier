from django.core.management.base import BaseCommand, CommandError
from events.models import ScrapedEvent

class Command(BaseCommand):
    # args = '<poll_id poll_id ...>'
    help = 'Loads scraped events from the scraped view'

    def handle(self, *args, **options):
        try:
            for e in ScrapedEvent.objects.all(): e.to_event()
        except e:
            raise CommandError(e)

        self.stdout.write('Successfully loaded scraped events')