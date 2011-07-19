from django.views.generic import DetailView
from events.models import Event

class EventDetailView(DetailView):
    context_object_name = 'event'

    def get_queryset(self):
        qs = Event.objects.select_related('summary')
        return qs.filter(
            slug__iexact=self.kwargs['slug'],
            secret_key__iexact=self.kwargs['secret_key']
        )

    def get_context_data(self, **kwargs):
        ctx = super(EventDetailView, self).get_context_data(**kwargs)
        event = ctx['event']
        # earliest occurence TODO refactor to handle multi-occurrence
        ctx['occurrence'] = event.occurrences \
            .select_related('place__point__city') \
            .order_by('-start_date', '-start_time')[0]
        return ctx
