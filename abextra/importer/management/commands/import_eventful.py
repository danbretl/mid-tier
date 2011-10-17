from django.core.management.base import BaseCommand, CommandError
from importer.parsers.event import EventParser
from importer.eventful_import import EventfulImporter 
from optparse import make_option
from events.models import Event

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--page-size',
            action='store',
            dest='page_size',
            default=10,
            help='Amount of events per page to fetch'),
        make_option('--total-pages',
            action='store',
            dest='total_pages',
            default=2,
            help='Total pages of events to fetch'),
        make_option('--page-offset',
            action='store',
            dest='page_offset',
            default=1,
            help='Page_offset to start on'),
        make_option('--dry-run',
            action='store_true',
            dest='dry_run',
            default=True,
            help='Save to db or not'),
        make_option('--mock-api',
            action='store_true',
            dest='mock_api',
            default=False,
            help='Use mock API class'),
        make_option('--make-dumps',
            action='store_true',
            dest='make_dumps',
            default=False,
            help='Use mock API class'),
        make_option('--interactive',
            action='store_true',
            dest='interactive',
            default=False,
            help='Import events in interactive mode')
        )
    help = 'Loads scraped object generated by eventful'

    def handle(self, **options):
        page_offset = int(options['page_offset'])
        page_size = int(options.get('page_size'))
        total_pages = int(options.get('total_pages'))
        interactive = options.get('interactive')
        make_dumps = options.get('make_dumps')
        mock_api = options.get('mock_api')

        try:
            importer = EventfulImporter(page_size=page_size,
                    current_page=page_offset, mock_api=mock_api,
                    interactive=interactive,make_dumps=make_dumps, total_pages=total_pages)
            results = importer.import_events()

            # FIXME should prolly happen automagically elsewhere
            for e in Event.objects.filter(id__in=[event_id for created, event_id in results]):
                e.save()

        except Exception, e:
            raise CommandError(e)
        else:
            self.stdout.write('Successfully imported eventful API results')
