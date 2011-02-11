from django.test import TestCase
from django.contrib.auth.models import User
from events.models import Category, Event
from behavior.models import EventAction, EventActionAggregate


class EventActionAggregateTest(TestCase):
    fixtures = ['auth', 'categories']

    def setUp(self):
        user = User.objects.get(username='tester_api')
        category = Category.objects.get(id=1)

        self.aggr = EventActionAggregate.objects.create(
            user=user,
            category=category
        )

    def test_initialized_with_zero_counts(self):
        action_counts = (getattr(self.aggr, a) for a in 'gvix')
        self.assertTrue(all(map(lambda x: x == 0, action_counts)))

    def test_update_action_count_in_mem(self):
        self.aggr.update_action_count('G')
        self.assertEqual(self.aggr.g, 1)

        self.aggr.update_action_count('x', 5)
        self.aggr.update_action_count('x', -3)
        self.assertEqual(self.aggr.x, 2)

        reloded_aggr = EventActionAggregate.objects.get(id=self.aggr.id)
        action_counts = (getattr(reloded_aggr, a) for a in 'gvix')
        self.assertTrue(all(map(lambda x: x == 0, action_counts)))

    def test_update_action_count_persist(self):
        self.aggr.update_action_count('G')
        self.aggr.update_action_count('x', -3, commit=True)

        reloaded_aggr = EventActionAggregate.objects.get(id=self.aggr.id)
        action_counts = [getattr(reloaded_aggr, a) for a in 'gvix']
        self.assertEqual(action_counts, [1, 0, 0, -3])

    def tearDown(self):
        self.aggr.delete()


class UpdateAggregateBehaviorSignalTest(TestCase):
    fixtures = ['auth', 'categories', 'events']

    def setUp(self):
        user = User.objects.get(username='tester_api')
        event = Event.objects.get(id=1)
        # categorize events with with the first four cats
        categories = Category.objects.filter(id__in=(1,2,3,4))
        for category in categories:
            event.categories.add(category)
        self.user = user
        self.categories = categories
        self.event = event

    def test_update_with_existing(self):
        """
        User has preexisting aggregates which should be properly handled.
        If event action is `fresh`, do a simple +1 count for the categories.
        If event action is a `change` of action, do a -1 count for the old action
        and +1 for the new action.
        """
        # setup some existing aggregates
        for category in self.categories[:2]:
            EventActionAggregate(user=self.user, category=category, i=1).save()

        # insert a new event action
        EventAction(user=self.user, event=self.event, action='I').save()

        # make some assertions
        user_agg_qs_base = EventActionAggregate.objects.filter(user=self.user)
        user_agg_qs_exist = user_agg_qs_base.filter(category__in=self.categories[:2])
        user_agg_qs_fresh = user_agg_qs_base.filter(category__in=self.categories[2:])

        self.assertEqual(user_agg_qs_base.count(), 4)
        self.assertEqual(user_agg_qs_exist.filter(g=0, v=0, i=2, x=0).count(), 2)
        self.assertEqual(user_agg_qs_fresh.filter(g=0, v=0, i=1, x=0).count(), 2)

        # update the same event
        event_action = EventAction.objects.get(user=self.user, event=self.event)
        event_action.action = 'X'
        event_action.save()

        # make some assertions
        self.assertEqual(user_agg_qs_base.count(), 4)
        self.assertEqual(user_agg_qs_exist.filter(g=0, v=0, i=1, x=1).count(), 2)
        self.assertEqual(user_agg_qs_fresh.filter(g=0, v=0, i=0, x=1).count(), 2)
