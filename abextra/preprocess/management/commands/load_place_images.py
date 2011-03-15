import os

from django.core.files import File
from django.core.management.base import NoArgsCommand, CommandError
from django.conf import settings

from places.models import Place
from preprocess.models_external import Location as PlaceExt


class Command(NoArgsCommand):
    help = 'Import images from scrapery.'

    def handle(self, **options):
        try:

            for place in Place.objects.all():
                place_ext = PlaceExt.objects.get(id=place.id)
                if place_ext.image_path:
                    path = os.path.join(
                        settings.SCRAPE_IMAGES_PATH,
                        place_ext.image_path
                    )
                    with open(path) as f:
                        place.image.save(os.path.split(f.name)[1], File(f))

        except Exception, e:
            raise CommandError(e)
        self.stdout.write('Successfully loaded place images.\n')