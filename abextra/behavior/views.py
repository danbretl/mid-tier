from django.http import HttpResponse, HttpResponseNotAllowed
from api.urls import auth
from piston.utils import rc

from behavior.models import EventAction
from behavior.forms import EventActionForm

def require_auth(func):
    """Decorator for requiring authentication."""
    def new_func(request, *args, **kwargs):
        if not getattr(request, 'user', False) or not auth.is_authenticated(request):
            return auth.challenge()
        else:
            return func(request, *args, **kwargs)
    return new_func

@require_auth
def create_eventaction(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    data=dict(request.POST.iteritems())
    data.update(user=request.user.id)
    try:
        event_action = EventAction.objects.get(user=data['user'], event=data['event'])
        f = EventActionForm(data=data, instance=event_action)
    except EventAction.DoesNotExist:
        f = EventActionForm(data=data)

    if f.is_valid():
        f.save()
        return rc.CREATED
    else:
        return rc.BAD_REQUEST
