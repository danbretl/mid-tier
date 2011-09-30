from django.core.management.base import BaseCommand, CommandError
from importer.parsers.event import EventParser
from importer.eventful_import import EventfulImporter 
from optparse import make_option

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--page-size',
            action='store',
            dest='page_size',
            default=100,
            help='Amount of events per page to fetch'),
        make_option('--total-pages',
            action='store',
            dest='total_pages',
            default=5,
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

        )
    help = 'Loads scraped object generated by eventful'

    def handle(self, **options):
        # try:
        page_offset = options.get('page_offset')
        importer = EventfulImporter(page_size=int(options.get('page_size')))
        events = importer.import_events(total_pages=int(options.get('total_pages')))
        # except Exception as e:
            # import ipdb; ipdb.set_trace()
            # raise CommandError(e) 
