from django.core.management.base import NoArgsCommand
from behavior.models import EventAction
from collections import defaultdict
import datetime

class Command(NoArgsCommand):
    help = 'Recalculate popularity for events based on users over the last 30 days'

    def handle(self, **options):
        event_score = defaultdict(int)
        past_instant = datetime.timedelta(days=-31) + datetime.date.today()
        event_acts = EventAction.objects.filter(timestamp__gte=past_instant)
        for event_action in event_acts.filter(action='G'):
            event_score[event_action.event] += 3

        for event_action in event_acts.filter(action='V'):
            event_score[event_action.event] += 1

        for event in event_score.keys():
            event.popularity_score = event_score[event]
            event.save()



