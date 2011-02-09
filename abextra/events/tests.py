from django.test import TestCase
from events.models import Category
from events.utils import CachedCategoryTree

class TestCategoryTree(TestCase):
    fixtures = ['categories.json']

    def setUp(self):
        self.ctree = CachedCategoryTree()

    def test_convenience(self):
        concretes = set(self.ctree.all_concrete())
        abstracts = set(self.ctree.all_abstract())
        self.assertTrue(concretes)
        self.assertTrue(abstracts)
        self.assertFalse(concretes & abstracts)

    def test_category_retreival(self):
        title = 'concerts'
        cdb = Category.objects.get(title=title)
        cmem = self.ctree.category_by_title(title)
        self.assertEqual(cdb, cmem)

from django.contrib.auth.models import User
from events.models import Category

from learning import ml, settings, CategoryTree

class MLModuleTest(TestCase):
    """
    This module tests the ML algorithm functions
    """
    fixture = ["categories.json"]
    def setUp(self):
        self.unitArray = [1] * 10
        self.emptyArray = []
        self.rangeArray = range(100)

    def test_normalize(self):
        self.assertEqual(ml.normalize(self.unitArray), [1.0 / len(self.unitArray)] * len(self.unitArray))
        self.assertEqual(ml.normalize(self.emptyArray), [])
        self.assertEqual(ml.normalize(self.rangeArray), [(x * 2.0) / (len(self.rangeArray) * (len(self.rangeArray) - 1)) for x in self.rangeArray])

    def test_scoring_function(self):
        #Given a 4 tuple always returns a float
        #Given no input errors out
        #test the learning constant etc.
        None

    def test_topN_function(self):
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

    def test_probabilistic_walk(self):
        #invariants:
        # Total scores sum up to 1.0 after walk for any label
        userTree = CategoryTree.CategoryTree(self.user)
        userTree.top_down_recursion(ml.scoring_function,{"outkey":"score"})
        userTree.top_down_recursion(ml.probabilistic_walk,{"inkey":"score", "outkey":"probabilistic_walk"})
        print "simple_probability sum is: ", userTree.subtree_score("probabilistic_walk")
        self.assertAlmostEqual(1.0,userTree.subtree_score("probabilistic_walk"))
        userTree.bottom_up_recursion(ml.topN_function,{"inkey":"score","outkey":"topNscore"})
        userTree.top_down_recursion(ml.probabilistic_walk,{"inkey":"topNscore", "outkey":"topNscore_probability"})
        print "topNscore_probability sum is: ", userTree.subtree_score("topNscore_probability")
        print "Current Dictionary: "
        userTree.print_dictionary_key_values()
        self.assertAlmostEqual(1.0,userTree.subtree_score("topNscore_probability"))

    def test_convergence(self):
        # import ipdb; ipdb.set_trace()
        categories = ml.recommend_categories(self.user)
        print "Categories: ", categories
        picked_category = Category.objects.get(id=categories[0])

        picked_aggr = EventActionAggregate(user=self.user, category=picked_category)
        picked_aggr.save()

        while True:
            count = self.count.next()
            print count
            if count > 100:
                self.assertTrue(False)

            # recommend a new set of categories
            cats = ml.recommend_categories(self.user)
            cnt = 0
            for i in cats:
                if i == picked_category.id:
                    cnt += 1
            cats = set(cats)

            print "Categories: ",cats
            print "ID: ", picked_category.id
            print "Count: ", cnt

            cats.discard(picked_category.id)
            
            # # G(oto) picked category
            picked_aggr.g += cnt
            picked_aggr.save()

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

            if count == 50 or count == 80:
                import pdb; pdb.set_trace()

        self.assertTrue(True)

class CategoryTest(TestCase):

    def setUp(self):
        None

    def test_scoring_function(self):
        None
        

        

