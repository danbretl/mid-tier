import os

from django.core.files import File
from django.core.management.base import NoArgsCommand, CommandError
from django.conf import settings

from events.models import Event
from preprocess.models_external import Event as EventExt


class Command(NoArgsCommand):
    help = 'Import images from scrapery.'

    def handle(self, **options):
        try:

            for event in Event.objects.all():
                event_ext = EventExt.objects.get(guid=event.xid)
                if event_ext.image_path:
                    path = os.path.join(
                        settings.SCRAPE_IMAGES_PATH,
                        event_ext.image_path
                    )
                    with open(path) as f:
                        event.image.save(os.path.split(f.name)[1], File(f))

        except Exception, e:
            raise CommandError(e)
        self.stdout.write('Successfully loaded event images.\n')