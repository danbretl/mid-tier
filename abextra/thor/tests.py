from django.test import TestCase
from thor import settings, user_behavior, testing_simulation, testing_framework
from thor import simulation_shared, ml
from thor.category_tree import CategoryTree
from matplotlib import pyplot as plt
from django.contrib.auth.models import User
from events.models import Event, Category
from behavior.models import EventActionAggregate
from itertools import count
from scipy.stats import binom_test
from events.utils import CachedCategoryTree
import random

class AlgorithmTest(TestCase):
    """test for ml algorithms"""
    fixtures = ['auth', 'categories', 'default_behavior','places', 'events']
    def setUp(self):
        self.count = count()
        self.user = User.objects.get(username='tester_api')
        #MockInitializer().run()

    def test_probabilistic_walk(self):
        #invariants:
        # Total scores sum up to 1.0 after walk for any label
        userTree = category_tree.CategoryTree(self.user)
        userTree.top_down_recursion(ml.scoring_function,{"outkey":"score"})
        userTree.top_down_recursion(ml.probabilistic_walk,{"inkey":"score", "outkey":"probabilistic_walk"})
        #print "simple_probability sum is: ", userTree.subtree_score("probabilistic_walk")
        self.assertAlmostEqual(1.0,userTree.subtree_score("probabilistic_walk"))
        userTree.bottom_up_recursion(ml.topn_function,{"inkey":"score","outkey":"topNscore"})
        userTree.top_down_recursion(ml.probabilistic_walk,{"inkey":"topNscore", "outkey":"topNscore_probability"})
        #print "topNscore_probability sum is: ", userTree.subtree_score("topNscore_probability")
        #print "Current Dictionary: "
        userTree.print_dictionary_key_values()
        self.assertAlmostEqual(1.0,userTree.subtree_score("topNscore_probability"))

    def test_framework(self):
        user = testing_framework.EventureUser()
        user.calculate_plot_metrics(1)


    def test_multi_category_recall(self,user=None):
        if not user:
            user = self.user
        for c in Category.objects.all():
            EventActionAggregate(user=user,category=c).save()

        # Each color corresponds to the number of categories (position in list + 1) selected during the iteration.
        colors = ["r","b","g","k","c","m","y"]
        # k is the number of categories selected.
        for k in range(1,8):
            categories = set(ml.recommend_categories(user))
            picked_categories = set(random.sample(categories,k))
            print "User picked categories: ", picked_categories
            # Generate mapping between categories and User's event action aggregate (GVIX store)
            picked_cat_aggregates = dict([(c,EventActionAggregate.objects.get(user=user, category=c)) for c in picked_categories])
            trials = count()
            lst = []
            while trials.next() < 50:
                print "Loop: ", trials
                mean_loop_count = count()
                recall = 0
                iterations = 10
                G = {}           #temporary dictionary that store G counts for selected categories during iterations.
                while mean_loop_count.next() < iterations:
                    cats = set(ml.recommend_categories(user))
                    correct_recommendations = cats.intersection(picked_categories)
                    for c in correct_recommendations:
                        try:
                            G[c] += 1
                        except:
                            G[c] = 1
                        #picked_cat_aggregates[x].save()
                        cats.discard(picked_cat_aggregates[c])
                    #end of looping over correct_recommendations
                    recall += len(correct_recommendations)*100.0/len(picked_categories)
                #end of looping over iterations to calculate means.

                #####
                #print "Recall: ", recall
                #set and save the x values of discarded categories to the average number of times the category was G'd over iterations.
                for key,value in G.iteritems():
                    picked_cat_aggregates[key].g += min(round(value/iterations),2)
                    picked_cat_aggregates[key].save()
                #end of looping over temporary dictionary.

                lst.append(recall*1.0/iterations)

                #Variant 1: All items in the last iterations that were not in the picked category have been X'd once.
                for c in cats:
                    try:
                        eaa = EventActionAggregate.objects.get(user=user, category=c)
                    except EventActionAggregate.DoesNotExist:
                        eaa = EventActionAggregate(user=user, category=c)
                    eaa.x += 1
                    eaa.save()
                #end of adding X's
                #end
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
        plt.savefig("thor/test_results/recall.pdf")
        plt.cla()
        #import pdb; pdb.set_trace()
        self.assertTrue(True)


    def test_convergence(self):
        categories = ml.recommend_categories(self.user)
        #print "Categories: ", categories
        picked_category = ml.sample_distribution(categories.items())[0]
        #print "picked category: ", picked_category
        picked_aggr = EventActionAggregate(user=self.user, category=picked_category)
        lst = []
        ctree = CachedCategoryTree()
        parents = ctree.parents(picked_category)
        count = 0
        while count < 100:
            count +=1
            print "Round: %d\r"%count,
            sys.stdout.flush()
            # recommend a new set of categories
            recommendation_scores =  ml.recommend_categories(self.user)
            cats = ml.sample_category_distribution(recommendation_scores.items(),
                                          settings.N)
            found_count = cats.count(picked_category)

            #print "Categories: ",cats
            #print "ID: ", picked_category.id
            cats = set(cats)
            cats.discard(picked_category.id)

            # # G(oto) picked category
            picked_aggr.g += found_count
            picked_aggr.save()

            # X all other categories
            for c in cats:
                if c in parents:
                    continue
                try:
                    eaa = EventActionAggregate.objects.get(user=self.user, category=c)
                except EventActionAggregate.DoesNotExist:
                    eaa = EventActionAggregate(user=self.user, category=c)
                eaa.x += 1
                eaa.save()

            lst.append(found_count*100.0/settings.N)
        plt.plot(lst,color="blue")
        plt.title("Rate of learning one category")
        plt.xlabel("Trials")
        plt.ylabel("% of all Recommendations")
        plt.savefig("thor/test_results/test.pdf")
        plt.cla()
        self.assertTrue(True)


class PersonTest(TestCase):
    """
    tests for the Person framework for simulating preferences and testing
    the ML algorithm.
    """
    # right now categories, not events, are used
    fixtures = ['auth', 'categories']

    def setUp(self):
        """initialize behavior db"""
        self.user = User.objects.get(id=1)
        self.db = user_behavior.UserBehaviorDict()
        self.db.initialize_user(self.user)

    def __run_and_test_rounds(self, person, num_rounds, num_trials,
                                    num_recommendations=settings.N):
        """
        run the given person for the given number of rounds, and then
        check consistency- number of trials, rounds, recommendations, etc.
        Not specific to one type of Person
        """
        person.run_rounds(num_rounds, num_trials, num_recommendations)

        # test number of rounds, trials, recommendations
        self.assertEqual(len(person.rounds), num_rounds)
        self.assertTrue(all([len(r) == num_trials for r in person.rounds]))
        for round in person.rounds:
            self.assertTrue(all([r.N == num_recommendations == len(r.actions)
                                for r in round]))

        # check that it can't run more than once
        # Fixme
        #self.assertRaises(testing_simulation.SimulationError,
        #                  person.run_rounds, (1, 1))

    def test_deterministic_person(self):
        """
        test the simulation where a person always goes to specific
        categories and always X's others
        """
        # first, try a bunch of simple tests of the get_action behavior
        all_categories = range(1, 10)
        liked = random.sample(all_categories, 3)
        simple_p = testing_simulation.DeterministicPerson(liked,
                                                        user=self.user,
                                                        behavior_db=self.db)
        for c in all_categories:
            self.assertEqual(simple_p.get_action(c),
                             simulation_shared.GO if c in liked else simulation_shared.XOUT)

        # now more realistic tests with real category IDs
        categories = ['Bars','Clubs', 'Plays','Sculpture','Fallon', 'Wine',
                      'Sculpture']
        category_ids = map(testing_simulation.get_category_id, categories)
        person = testing_simulation.DeterministicPerson(category_ids,
                                                        behavior_db=self.db)

        # this should take under 1 second to run with the custom db, and
        # more like 30 seconds with the regular DB
        self.__run_and_test_rounds(person, 50, 2)

        # for each round, check that it had the correct behavior
        for rlst in person.rounds:
            for r in rlst:
                for c, a in zip(r.recommendations, r.actions):
                    if c in category_ids:
                        self.assertEquals(a, simulation_shared.GO)
                    else:
                        self.assertEquals(a, simulation_shared.XOUT)

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

    def test_sampling_distribution(self):
        """
        test if the sampling distribution function is working as expected.
        """
        trials = 1000
        distribution = [('H',0.5),('T',0.5)]
        num_heads = ml.sample_distribution(distribution,trials).count('H')
        result = [binom_test(num_heads,trials,1.0/2) for x in range(trials)]
        mean = sum(result) / len(result)
        # NOTE: Maybe this number should be higher. What is a good number?
        self.assertTrue(mean > 0.05)

    def test_semi_sort(self):
        k = 10000
        for i in range(2,5):
            lst = range(k)
            random.shuffle(lst)
            self.assertEqual(set(ml.semi_sort(lst, i)[:i]), set(range(k)[-i:]))

class CategoryTreeTest(TestCase):
    fixtures = ['categories', 'users', 'auth']

    def setUp(self):
        self.user = User.objects.get(id=1)
        self.category_tree = CategoryTree(self.user.id)

    def test_init(self):
        self.assertRaises(TypeError, CategoryTree)
        # Also test with different combinations of parameters.

    def test_get_all_category_scores_dictionary(self):
        self.assertRaises(TypeError,
                          self.category_tree.get_all_category_scores_dictionary)

    def test_get_parent(self):
        self.assertEqual(None, self.category_tree.parent)
        for children in self.category_tree.children:
            self.assertEqual(children.parent, self.category_tree)

    def test_get_children(self):
        children = Category.objects.filter(parent=self.category_tree.category)
        test_result = [child.category for child in self.category_tree.children]
        self.assertEqual(set(children), set(test_result))

    def test_insert_key_value(self):
        self.assertRaises(TypeError, self.category_tree.insert_key_value)
        self.assertRaises(TypeError,
                          self.category_tree.insert_key_value,
                          'param1')
        self.assertRaises(TypeError,
                          self.category_tree.insert_key_value,
                          'param1', 'param2', 'param3')
        key_values = [('XYZ', 1), ('ABC', '2'), ('cde',(1,2))]
        for key, value in key_values:
            self.category_tree.insert_key_value(key, value)
        self.assertEqual(self.category_tree.dictionary, dict(key_values))

    def test_get_key_value(self):
        self.assertRaises(TypeError, self.category_tree.get_key_value)
        self.assertRaises(TypeError, self.category_tree.get_key_value, 1, 2)
        self.assertEqual(self.category_tree.get_key_value(1), None)
        key_values = [('XYZ', 1), ('ABC', '2'), ('cde',(1,2))]
        for key, value in key_values:
            self.category_tree.insert_key_value(key, value)
            self.assertEqual(value, category_tree.get_key_value(key))

    def test_subtree_score(self):
        self.assertRaises(TypeError,self.category_tree.subtree_score)
        self.assertRaises(TypeError,self.category_tree.subtree_score, 1, 2)
        total = self.recursion_test(self.category_tree)
        self.assertEqual(total, self.category_tree.subtree_score('score'))

    def test_topdown_recursion(self):
        # Need to come up with a creative solution to test these
        # Any test I have come up with replicates the same code in the module
        # and therefore isn't a sound test.
        pass

    def test_bottomup_recursion(self):
        pass

    def test_repr(self):
        pass

    def test_print_dictionary_key_values(self):
        pass
