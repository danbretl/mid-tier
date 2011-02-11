from django.test import TestCase
from events.models import Category
from events.utils import CachedCategoryTree
from matplotlib import pyplot as plt
import random

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
    fixtures = ['auth', 'categories', 'default_behavior']
    def setUp(self):
        self.count = count()
        self.user = User.objects.get(username='tester_api')

    def test_probabilistic_walk(self):
        #invariants:
        # Total scores sum up to 1.0 after walk for any label
        userTree = CategoryTree.CategoryTree(self.user)
        userTree.top_down_recursion(ml.scoring_function,{"outkey":"score"})
        userTree.top_down_recursion(ml.probabilistic_walk,{"inkey":"score", "outkey":"probabilistic_walk"})
        #print "simple_probability sum is: ", userTree.subtree_score("probabilistic_walk")
        self.assertAlmostEqual(1.0,userTree.subtree_score("probabilistic_walk"))
        userTree.bottom_up_recursion(ml.topN_function,{"inkey":"score","outkey":"topNscore"})
        userTree.top_down_recursion(ml.probabilistic_walk,{"inkey":"topNscore", "outkey":"topNscore_probability"})
        #print "topNscore_probability sum is: ", userTree.subtree_score("topNscore_probability")
        #print "Current Dictionary: "
        userTree.print_dictionary_key_values()
        self.assertAlmostEqual(1.0,userTree.subtree_score("topNscore_probability"))

    def test_multi_category_recall(self,user=None):
        if not user:
            user = self.user
        for c in Category.objects.all():
            EventActionAggregate(user=user,category=c).save()

        colors = ["r","b","g","k","c","m","y"]

        for k in range(1,8):
            categories = set(ml.recommend_categories(user))
            picked_categories = set(random.sample(categories,k))
            print "Picked categories: ", picked_categories
            #print "Selected categories: ", picked_categories
            picked_cat_aggregates = dict([(p,EventActionAggregate.objects.get(user=user, category=p)) for p in picked_categories])
            loop_count = 0
            lst = []
            while loop_count < 50:
                loop_count+=1
                #print "Loop: ", loop_count
                cats = ml.recommend_categories(user)
                picked_cat_count = 0
                category_count_map = {}

                for i in cats:
                    if i in picked_categories:
                        try:
                            category_count_map[i] +=1
                        except:
                            category_count_map[i] = 1
                            
                cats = set(cats)
#                print "Recommendations: ", cats

                correct_recommendations = cats.intersection(picked_categories)
                for x in correct_recommendations:
                    picked_cat_aggregates[x].g += 1 #category_count_map[x]
                    picked_cat_aggregates[x].save()
                    cats.discard(picked_cat_aggregates[x])

                print "recommendations: ", correct_recommendations

                recall = len(correct_recommendations)*100.0/len(picked_categories)
                #print "Recall: ", recall
                lst.append(recall)

                for c in cats:
                    try:
                        eaa = EventActionAggregate.objects.get(user=user, category=c)
                    except EventActionAggregate.DoesNotExist:
                        eaa = EventActionAggregate(user=user, category=c)
                    eaa.x += 1
                    eaa.save()
                    
            print "Recall: ",lst
            plt.plot(lst,color=colors[k-1],label=k)       
            for c in Category.objects.all():
                #import pdb; pdb.set_trace()
                try:
                    eaa = EventActionAggregate.objects.get(user=user, category=c)
                    eaa.g = 0
                    eaa.v = 0
                    eaa.i = 0
                    eaa.x = 0
                    eaa.save()
                except:
                    pass
                    

        plt.title("Recall")
        plt.xlabel("Trials")
        plt.ylabel("% of User preferred categories")
        #plt.legend()
        plt.savefig("recall.pdf")
        #import pdb; pdb.set_trace()
        self.assertTrue(True)


    def test_convergence(self):
        # import ipdb; ipdb.set_trace()
        categories = ml.recommend_categories(self.user)
        #print "Categories: ", categories
        picked_category = categories[0]
        
        picked_aggr = EventActionAggregate(user=self.user, category=picked_category)
        #picked_aggr.save()
        lst = []
    
        count = 0
        while count < 50:
            count +=1
            #print count
            # recommend a new set of categories
            cats = ml.recommend_categories(self.user)
            cnt = 0
            for i in cats:
                if i == picked_category:
                    cnt += 1

            #print "Categories: ",cats
            #print "ID: ", picked_category.id
            #print "Count: ", cnt

            cats = set(cats)
            cats.discard(picked_category.id)
            
            # # G(oto) picked category
            picked_aggr.g += cnt
            picked_aggr.save()
            
            # X all other categories
            for c in cats:
                try:
                    eaa = EventActionAggregate.objects.get(user=self.user, category=c)
                except EventActionAggregate.DoesNotExist:
                    eaa = EventActionAggregate(user=self.user, category=c)
                eaa.x += 1
                eaa.save()
                    
            lst.append(cnt*100.0/settings.N)
        lst.append(100.0)
        plt.plot(lst,color="blue")
        plt.title("Rate of learning one category")
        plt.xlabel("Trials")
        plt.ylabel("% of all Recommendations")
        plt.savefig("test.pdf")
        self.assertTrue(True)


class CategoryTest(TestCase):

    def setUp(self):
        None

    def test_scoring_function(self):
        None
        

        

