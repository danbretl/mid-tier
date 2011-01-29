from django.test import TestCase
from django.contrib.auth.models import User
from events.models import Category
from behavior.models import EventActionAggregate
from behavior.utils import update_aggregate_behavior


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


# class UpdateAggregateBehaviorTest(TestCase):
#     fixtures = ['auth.json', 'categories.json']
# 
#     def setUp(self):
#         user = User.objects.get(username='tester_api')
