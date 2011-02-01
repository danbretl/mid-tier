from django.http import HttpResponse, HttpResponseNotAllowed
from api.urls import auth
from piston.utils import rc

from behavior.models import EventAction
from behavior.forms import EventActionForm
from behavior.utils import reset_user_behavior

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

    # the forms are case sensitive
    action = data.get('action')
    if action:
        data['action'] = action.upper()

    f = EventActionForm(data=data)
    if f.is_valid():
        inst = f.instance
        try:
            event_action = EventAction.objects.get(user=inst.user, event=inst.event)
        except EventAction.DoesNotExist:
            event_action = inst
        else:
            event_action.action = inst.action
        event_action.save()
        return rc.CREATED
    else:
        return rc.BAD_REQUEST

# FIXME this is a very dangerous request handler
# FIXME perhaps we should make it a post or something :: just for an impression of 
@require_auth
def reset_behavior(request):
    """
    Resets behavior by clearing all user's event actions and hence action
    aggregates.
    """
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    reset_user_behavior(request.user)
    return rc.ALL_OK
