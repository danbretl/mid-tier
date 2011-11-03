from django.test import TestCase
from django.contrib.auth.models import User
from events.models import Category, Event
from behavior.models import EventAction, EventActionAggregate
from django_dynamic_fixture import get


class EventActionAggregateTest(TestCase):
    def setUp(self):
        self.aggr = get(EventActionAggregate)

    def test_initialized_with_zero_counts(self):
        self.assertTupleEqual((0,0,0,0), self.aggr.as_tuple(), 'GVIX initialized with non-zero values')

    def test_update_action_count_in_mem(self):
        self.aggr.update_action_count('G')
        self.assertEqual(self.aggr.g, 1)

        self.aggr.update_action_count('x', 5)
        self.aggr.update_action_count('x', -3)
        self.assertEqual(self.aggr.x, 2)

        reloded_aggr = EventActionAggregate.objects.get(id=self.aggr.id)
        self.assertTupleEqual((0,0,0,0), reloded_aggr.as_tuple(), 'GVIX update unexpected persist')

    def test_update_action_count_persist(self):
        self.aggr.update_action_count('G')
        self.aggr.update_action_count('x', -3, commit=True)

        reloaded_aggr = EventActionAggregate.objects.get(id=self.aggr.id)
        self.assertTupleEqual((1,0,0,-3), reloaded_aggr.as_tuple(), 'Unexpected GVIX values')


class UpdateAggregateBehaviorSignalTest(TestCase):
    def setUp(self):
        self.categories = get(Category, n=4)
        self.event = get(Event, categories=self.categories)
        self.user = get(User)

    def test_update_with_existing(self):
        """
        User has preexisting aggregates which should be properly handled.
        If event action is `fresh`, do a simple +1 count for the categories.
        If event action is a `change` of action, do a -1 count for the old action
        and +1 for the new action.
        """
        # setup some existing aggregates
        for category in self.categories[:2]:
            EventActionAggregate.objects.create(user=self.user, category=category, i=1)

        # insert a new event action
        EventAction.objects.create(user=self.user, event=self.event, action='I')

        # make some assertions
        user_agg_qs_base = EventActionAggregate.objects.filter(user=self.user)
        user_agg_qs_exist = user_agg_qs_base.filter(category__in=self.categories[:2])
        user_agg_qs_fresh = user_agg_qs_base.filter(category__in=self.categories[2:])

        # self.assertEqual(user_agg_qs_base.count(), 4)
        self.assertEqual(user_agg_qs_exist.filter(g=0, v=0, i=2, x=0).count(), 2)
        self.assertEqual(user_agg_qs_fresh.filter(g=0, v=0, i=1, x=0).count(), 2)

        # update the same event
        event_action = EventAction.objects.get(user=self.user, event=self.event)
        event_action.action = 'X'
        event_action.save()

        # make some assertions
        self.assertEqual(user_agg_qs_exist.filter(g=0, v=0, i=1, x=1).count(), 2)
        self.assertEqual(user_agg_qs_fresh.filter(g=0, v=0, i=0, x=1).count(), 2)
