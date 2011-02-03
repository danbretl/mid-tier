from behavior.models import EventAction, EventActionAggregate

def reset_user_behavior(user, nuke_event_actions=False):
    """
    Clear all event actions? and event action aggregates.
    """
    if nuke_event_actions:
        EventAction.objects.filter(user=user).delete()
    EventActionAggregate.objects.filter(user=user).delete()
