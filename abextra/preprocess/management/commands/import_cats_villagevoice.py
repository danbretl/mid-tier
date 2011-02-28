from django.core.management.base import NoArgsCommand, CommandError

from preprocess.models import Source

class Command(NoArgsCommand):
    help = 'Import external categories from VillageVoice.'

    def handle(self, **options):
        try:
            source = Source.objects.villagevoice
        except Exception, e:
            raise CommandError(e)
        self.stdout.write('Successfully loaded categories from %s.\n' % source)