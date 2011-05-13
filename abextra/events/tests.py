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
    from thor import testing_simulation, testing_framework
from thor import ml, settings, category_tree, user_behavior, simulation_shared
from itertools import count
from api.models import Consumer
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
