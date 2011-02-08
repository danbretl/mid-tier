from django.test import TestCase
from django.contrib.auth.models import User
from events.models import Category

from learning import ml, settings, CategoryTree

class MLModuleTest(TestCase):
    """
    This module tests the ML algorithm functions
    """

    def setUp(self):
        self.unitArray = [1] * 10
        self.emptyArray = []
        self.rangeArray = range(100)
        None

    def test_normalize(self):
        self.assertEqual(ml.normalize(self.unitArray), [1.0 / len(self.unitArray)] * len(self.unitArray))
        self.assertEqual(ml.normalize(self.emptyArray), [])
        # self.assertEqual(ml.normalize(self.rangeArray), [(x * 2.0) / (len(self.unitArray) * (len(self.unitArray) - 1)) for x in self.rangeArray])

    def test_topN_function_generator(self):
        for k in [x + 1 for x in range(5)]:
            topkFunction = settings.topN_function(k)
            self.assertEqual(topkFunction(self.unitArray), 1.0)
            self.assertEqual(topkFunction(self.emptyArray), 0.0)
            self.assertEqual(topkFunction(self.rangeArray), settings.mean(self.rangeArray[-k:]))

from itertools import count
from behavior.models import EventActionAggregate
class AlgorithmTest(TestCase):
    """test for ml algorithms"""
    fixtures = ['auth.json', 'categories.json']
    def setUp(self):
        # defualt behavior setup
        u = User(username='default_behavior')
        u.save()
        for c in Category.objects.all():
            EventActionAggregate(user=u, category=c).save()

        self.count = count()
        self.user = User.objects.get(username='tester_api')

    def test_convergence(self):
        # import ipdb; ipdb.set_trace()
        categories = ml.recommend_categories(self.user)
        picked_category = Category.objects.get(id=categories[0])

        picked_aggr = EventActionAggregate(user=self.user, category=picked_category)
        picked_aggr.save()

        while True:
            count = self.count.next()
            print count
            if count > 100:
                self.assertTrue(False)

            # # G(oto) picked category
            picked_aggr.g += 1
            picked_aggr.save()

            # recommend a new set of categories
            cats = set(ml.recommend_categories(self.user))
            print cats, picked_category.id
            cats.discard(picked_category.id)

            # test converge
            if not cats: break

            # X all other categories
            for c in cats:
                try:
                    eaa = EventActionAggregate.objects.get(user=self.user, category=c)
                except EventActionAggregate.DoesNotExist:
                    eaa = EventActionAggregate(user=self.user, category=Category.objects.get(id=c))
                eaa.x += 1
                eaa.save()

        self.assertTrue(True)

# import random
# 
# from events import models as ems
# class EventureInitializer(object):
#     """factory class for initialization of eventure app"""
# 
#     def __init__(self, n_events=100, categories=None, cross_categorization=4):
#         super(EventureInitializer, self).__init__()
#         self.n_events = n_events
# 
#         # fetch necessary categories
#         c_base = ems.Category.objects
#         self.categories = c_base.filter(id__in=categories) if categories else c_base.all()
# 
#     def run(self):
#         pass

# from core.utils import Bunch
# CategoryNode = Bunch
# 
# for id, category in categories_by_id.iteritems():
#     # assign parent from the cache hash
#     parent_id = category.parent_id
#     category.parent = categories_by_id[parent_id] if parent_id else None
# 
#     # assign children
#     category.children = category_by_id
# 
# def _category_tree():
#     categories_by_id = dict((c.id, c) for c in Category.objects.all())
#     for id, category in categories_by_id.iteritems():
#         parent = categories_by_id.get(category.parent_id)
#         if parent:
#             category.parent = parent
#     return categories_by_id
# 
# def _concrete_category_tree():
#     categories_by_id = _category_tree()