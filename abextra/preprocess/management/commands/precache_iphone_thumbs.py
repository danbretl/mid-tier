from django.core.management.base import NoArgsCommand, CommandError

from api.utils import get_iphone_thumb

from events.models import Event
from events.utils import CachedCategoryTree


class Command(NoArgsCommand):
    help = 'Precache sorl thumbs for iPhone.'

    def handle(self, **options):
        try:
            ct = CachedCategoryTree()
            for e in Event.objects.all():
                get_iphone_thumb(e.image_chain(ct))

        except Exception, e:
            raise CommandError(e)
        self.stdout.write('Successfully precached images.\n')