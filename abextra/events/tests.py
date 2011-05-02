from django.test import TestCase
from django.contrib.auth.models import User
from django.test.client import Client
from events.models import Event, EventSummary, Category
from events import summarizer
from events.utils import CachedCategoryTree
try:
    from matplotlib import pyplot as plt
except ImportError:
    pass
else:
    from learning import testing_simulation, testing_framework
from learning import ml, settings, category_tree, user_behavior, simulation_shared
from itertools import count
from behavior.models import EventActionAggregate
from preprocess.utils import MockInitializer
from scipy.stats import binom_test
import sys
import random

class CachedCategoryTreeTest(TestCase):
    fixtures = ['categories']
    ctree = CachedCategoryTree()

    def test_get_by_title(self):
        title = 'Math and Science'
        cmem = self.ctree.get(title=title)
        cdb = Category.objects.get(title=title)
        self.assertEqual(cdb, cmem)

    def test_get_by_slug(self):
        slug = 'concerts'
        cmem = self.ctree.get(slug=slug)
        cdb = Category.objects.get(title=slug)
        self.assertEqual(cdb, cmem)

    def test_get_by_id(self):
        id = 10
        cmem = self.ctree.get(id=id)
        cdb = Category.objects.get(id=id)
        self.assertEqual(cdb, cmem)

    def test_convenience(self):
        self.assertTrue(self.ctree.concretes)
        self.assertTrue(self.ctree.abstracts)
        self.assertFalse(set(self.ctree.concretes) & set(self.ctree.abstracts))

class EventSummaryTest(TestCase):
    fixtures = ['events']

    def test_summarize_events(self):
        event = None
        x = summarizer.summarize_event(event, False)
        self.assertEquals(None, x)
        x = summarizer.summarize_event(event, True)
        self.assertEquals(None, x)

        # Confirm that event_summary information gets populated
        events = Event.objects.all().order_by('?')[:10]
        all_es = []
        for event in events:
            e_s = summarizer.summarize_event(event, True)
            occurrences = event.occurrences.all()
            if occurrences:
                self.assertNotEqual(e_s, None)
                #check if event related information is valid)
                self.assertEqual(e_s.title, event.title)
                self.assertEqual(e_s.id, event.id)
                self.assertEqual(e_s.concrete_category,
                                 event.concrete_category.title)
                self.assertEqual(e_s.title, event.title)
                self.assertEqual(e_s.url, event.url)
                self.assertEqual(e_s.description, event.description)

                #check if occurrence related information exists:
                self.assertNotEqual(e_s.time, None)
                self.assertNotEqual(e_s.place, None)
                self.assertNotEqual(e_s.date_range, None)
                self.assertNotEqual(e_s.price_range, None)
                all_es.append(e_s)
            else:
                self.assertEquals(None, e_s)

        # Confirm that event_summary information gets saved in DB
        all_inserted_es_set = set(all_es)
        event_ids = [ev.id for ev in events]
        all_DB_es_set = set(EventSummary.objects.filter(id__in=event_ids))
        self.assertEqual(all_inserted_es_set, all_DB_es_set)


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


class algorithm_profile(TestCase):
    """
    Profiling for ML algorithms.
    """
    fixtures = ['auth', 'categories', 'default_behavior','places', 'events']
    #fixtures = ['categories', 'default_behavior','places', 'events']
    def setUp(self):
        self.user = User.objects.get(id=1)

    def test_printing_precision_recall(self):
        """
        Note: this test is outdated. For right now algorithm tests remain in
        simple_testing.py (made debugging a lot easier, and the main reason
        for moving to testing framework was speeding up the DB, which was
        done using the user_behavior module
        """
        pass
        #c = testing_framework.EventureUser(self.user,categories=['Bars','Clubs','Musical','Poetry','Classic', 'Wine','Plays','Sculpture','Fallon'])
        #c.iterated_preferred_categories_plot(100,1)
        #self.assertTrue(True)
        #person = testing_simulation.DiscretePerson()
        #for i in range(100):
        #    person.push_recommendation()


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
        self.assertRaises(testing_simulation.SimulationError,
                          person.run_rounds, (1, 1))

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
                                                        db=self.db)
        for c in all_categories:
            self.assertEqual(simple_p.get_action(c),
                             simulation_shared.GO if c in liked else XOUT)

        # now more realistic tests with real category IDs
        categories = ['Bars','Clubs', 'Plays','Sculpture','Fallon', 'Wine',
                      'Sculpture']
        category_ids = map(testing_simulation.get_category_id, categories)
        person = testing_simulation.DeterministicPerson(category_ids,
                                                        db=self.db)

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
                        self.assertEquals(a, XOUT)


class UserBehaviorDBTest(TestCase):
    """
    test of the UserBehaviorDB classes, including UserBehaviorDict. Note that
    the UserBehaviorDjangoDB test has not yet been implemented
    """
    fixtures = ['auth', 'categories']

    def setUp(self):
        """initialize with some category ids"""
        categories = ['Bars','Clubs', 'Plays','Sculpture','Fallon', 'Wine',
                      'Sculpture']
        self.category_ids = map(testing_simulation.get_category_id, categories)

    def test_user_behavior_dict(self):
        """
        test the UserBehaviorDict, which is a class that stores user
        behavior not in a database but in a dictionary in memory
        """
        u = 1 # it doesn't actually matter if we have a real user or not
        db = user_behavior.UserBehaviorDict()
        self.__db_test(u, db)

    def test_user_behavior_django_db(self):
        """test the UserBehaviorDjangoDB class"""
        # TODO: THIS TEST HAS YET TO BE WRITTEN
        pass

    def __db_test(self, u, db):
        """given a user and a database, run through a bunch of tests by adding
        data and checking it at various points"""
        c1, c2, c3 = self.category_ids[:3]

        for i in range(10):
            db.perform_action(u, c1, simulation_shared.GO)
        self.assertEqual(db.gvix_dict(u)[c1], [10, 0, 0, 0])

        for i in range(20):
            db.perform_action(u, c1, simulation_shared.VIEW)
        self.assertEqual(db.gvix_dict(u)[c1], [10, 20, 0, 0])

        for i in range(50):
            db.perform_action(u, c2, simulation_shared.IGNORE)
            db.perform_action(u, c2, simulation_shared.XOUT)
        self.assertEqual(db.gvix_dict(u)[c2], [0, 0, 50, 50])

        # check that this hasn't affected others
        self.assertEqual(db.gvix_dict(u)[c3], [0, 0, 0, 0])

        # test clearing
        db.clear()

        for c in self.category_ids:
            self.assertEqual(db.gvix_dict(u)[c], [0, 0, 0, 0])

        # and finally, clear again
        db.clear()



class AlgorithmTest(TestCase):
    """test for ml algorithms"""
    fixtures = ['auth', 'categories', 'default_behavior','places', 'events']
    def setUp(self):
        self.count = count()
        self.user = User.objects.get(username='tester_api')
        #MockInitializer().run()

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
        user = TestingFramework.EventureUser()
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
        plt.savefig("learning/test_results/recall.pdf")
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
        plt.savefig("learning/test_results/test.pdf")
        plt.cla()
        self.assertTrue(True)


def test_concurrently(times):
    """ 
    Add this decorator to small pieces of code that you want to test
    concurrently to make sure they don't raise exceptions when run at the
    same time.  E.g., some Django views that do a SELECT and then a subsequent
    INSERT might fail when the INSERT assumes that the data has not changed
    since the SELECT.
    """
    def test_concurrently_decorator(test_func):
        def wrapper(*args, **kwargs):
            exceptions = []
            import threading
            def call_test_func():
                try:
                    test_func(*args, **kwargs)
                except Exception, e:
                    exceptions.append(e)
                    raise
            threads = []
            for i in range(times):
                threads.append(threading.Thread())
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            if exceptions:
                raise Exception('test_concurrently intercepted %s exceptions: %s' % (len(exceptions), exceptions))
        return wrapper
    return test_concurrently_decorator

class StressTesting(TestCase):
    """
    API's users will be hitting:
    1) Event_List
    2) Event_Detail
    3) CategoryFrequency
    4) BreadCrumbs
    5) Registration
    6) Sharing
    7) Haystack Search
    8) Event of the day page
    9) Event actions

    a) Test each API independently
    b) Test each API with a random ordering of the calls above
    c) Test each API with a expected sample of the calls above

    Serial stress test:
    a) Create a 1000 users
    b) For each of these users, generate a 100 requests
       - Randomly populate the user behavior db

    Concurrent stress test:
       - Same as above except, each user has his own process
         - Can a laptop handle 1000 processes?
           - Consider multithreading.

    To consider:
       - Distributed stress testing.

    Things to plot:
    a) Number of requests handled per second
    b) Average response time per request
    c) Users v/s load

    Stress testing individual components of the system:
    a) MySQL stress and performance tests under different query loads
    b) Django stress and performance tests under different query loads
       - Will be useful for before and after comparisons of Johnny Cache.
    c)
    """
    fixtures = ['auth', 'consumers']
    # Consider this for automated testing.
    def test_all_apis(self):
        base_url = 'http://testsv.abextratech.com'
        consumer_secret = '7fb49b90f41a832f3d5cc12f1b9ed56795c5748a'
        consumer_key = 'rngQ5ZSe3FmzYJ3cgL'
        udid = '6AAD4638-7E07-5A5C-A676-3D16E4AFFAF3'
        params = urllib.urlencode({'consumer_key' : consumer_key,
                                   'consumer_secret' : consumer_key,
                                   'udid' : udid,
                                   'format': 'json'})
        # The more automated we want to make this the less assumptions we will
        # need to make.
        f = urllib.urlopen(base_url + '/tapi/v1/?' + params)
        apis = json.loads(f.readline())
        for model in apis.keys():
            #Test apis here
            schema_url = apis[model]['schema']
            list_endpoint = apis[model]['list_endpoint']
            schema = json.loads(urllib.urlopen( base_url
                                              + schema_url
                                              + params).readline())
            # Now hit the url and get some objects.
            # Ensure each of the URLS conforms to this schema
            # (such checks will likely have also been performed in tastypie's
            # unit tests

    def simple_client(self):
        client = Client()
        consumer_secret = '7fb49b90f41a832f3d5cc12f1b9ed56795c5748a'
        consumer_key = 'rngQ5ZSe3FmzYJ3cgL'
        udid = '6AAD4638-7E07-5A5C-A676-3D16E4AFFAF3'
        encoded_params = urllib.urlencode({'consumer_key' : consumer_key,
                                   'consumer_secret' : consumer_key,
                                   'udid' : udid,
                                   'format': 'json'})

        params = '/tapi/v1/?' + encoded_params
        response = client.get(params)
        apis = json.loads(response.content)
        for model in apis.keys():
            schema_url = apis[model]['schema']
            list_endpoint = apis[model]['list_endpoint']
            api_schema_response = client.get( schema_url + '?' + encoded_params)
            print api_schema_response.content
            print "Schema: ", schema_url
