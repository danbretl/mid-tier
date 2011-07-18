from django.core.management.base import NoArgsCommand, CommandError
from django.conf import settings

from sorl.thumbnail import get_thumbnail

from events.models import Event
from events.utils import CachedCategoryTree

class Command(NoArgsCommand):
    help = 'Precache sorl thumbs for iPhone.'

    def handle(self, **options):
        try:
            ct = CachedCategoryTree()
            for e in Event.objects.all():
                image = e.image_chain(ct)
                get_thumbnail(image, **settings.IPHONE_THUMB_OPTIONS)

        except Exception, e:
            raise CommandError(e)
        self.stdout.write('Successfully precached images.\n')