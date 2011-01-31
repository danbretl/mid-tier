from django.test import TestCase
from django.contrib.auth.models import User
from events.models import Category, Event
from behavior.models import EventAction, EventActionAggregate


class EventActionAggregateTest(TestCase):
    fixtures = ['auth.json', 'categories.json']

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
    fixtures = ['auth.json', 'categories.json', 'events.json']

    def setUp(self):
        user = User.objects.get(username='tester_api')
        event = Event.objects.get(id=1)
        # categorize events with with the first four cats
        categories = Category.objects.filter(id__in=(1,2,3,4))
        for category in categories:
            event.categories.add(category)
        # setup some existing aggregates
        for category in categories[:2]:
            EventActionAggregate(user=user, category=category, g=1).save()
        self.user = user
        self.categories = categories
        self.event = event

    def test_update(self):
        EventAction(user=self.user, event=self.event, action='X').save()
        user_aggregates = EventActionAggregate.objects.filter(user=self.user)
        self.assertEqual(len(user_aggregates), 4)
