from django.core.management.base import BaseCommand
from django.conf import settings
from importer.api.eventful.paginator import EventfulPaginator
from optparse import make_option
from events.models import Event

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        # paginator args
        make_option('--interactive',
                    action='store_true',
                    dest='interactive',
                    default=False,
                    help='Import events in interactive mode'),
        make_option('--page-number',
                    action='store',
                    dest='page_number',
                    type='int',
                    help='Page to start on'),
        make_option('--total-pages',
                    action='store',
                    dest='total_pages',
                    type='int',
                    help='Total pages of events to fetch'),

        # consumer kwargs
        make_option('--mock-api',
                    action='store_true',
                    dest='mock_api',
                    default=False,
                    help='Use mock API class'),
        make_option('--make-dumps',
                    action='store_true',
                    dest='make_dumps',
                    default=False,
                    help='Make dumps of eventful client responses'),

        # query kwargs
        make_option('--page-size',
                    action='store',
                    dest='page_size',
                    type='int',
                    help='Amount of events per page to fetch'),

        # FIXME implement
        make_option('--dry-run',
                    action='store_true',
                    dest='dry_run',
                    default=True,
                    help='Save to db or not')
    )

    def handle(self, **options):
        #        try:
        filtered_dict = lambda src_dict, keys: dict((key, src_dict[key]) for key in
                filter(lambda k: src_dict.has_key(k) and not src_dict.get(k) == None, keys))
        consumer_kwargs = filtered_dict(options, ('make_dumps', 'mock_api'))
        query_kwargs = filtered_dict(settings.EVENTFUL_IMPORT_PARAMETERS, ('page_size', 'location', 'query', 'sort_order'))
        query_kwargs.update(filtered_dict(options,'page_size'))
        paginator_kwargs = filtered_dict(options, ('total_pages', 'page_number', 'interactive'))
        importer = EventfulPaginator(consumer_kwargs=consumer_kwargs, query_kwargs=query_kwargs, **paginator_kwargs)
        results = importer.import_events()

        # FIXME should prolly happen automagically elsewhere
        for e in Event.objects.filter(id__in=[event_id for created, event_id in results]):
            e.save()

        #        except Exception, e:
        #            raise CommandError(e)
        #        else:
        created_events_count = reduce(lambda count, result: count + int(result[0]), results, 0)
        self.stdout.write('Successfully imported eventful API results: %i total | %i created.\n' % (
            len(results), created_events_count)
        )
