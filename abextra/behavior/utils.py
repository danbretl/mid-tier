from behavior.models import EventActionAggregate

# FIXME needs to be much more optimized
# FIXME indexes on `action aggregate`{user_id, category_id}
# FIXME eager event / category relateds, see .select
# FIXME refactor for a bulk update
def update_aggregate_behavior(event_action):
    """
    Increases the aggregate count for a particular user's event action.
    Since, an event has multiple categories, we must update all aggregates
    accordingly.
    """
    event_categories = set(event_action.event.categories.all())
    aggregates = EventActionAggregate.objects.filter(
        user=event_action.user,
        category__in=event_categories
    )
    # process existing aggregates
    for aggregate in aggregates:
        event_categories.remove(aggregate.category)
        aggregate.update_action_count(event_action.action, commit=True)

    # process new aggregates (remaining in event categories)
    for category in event_categories:
        aggregate = EventActionAggregate(
            user=event_action.user,
            category=category
        ).update_action_count(event_action.action, commit=True)

