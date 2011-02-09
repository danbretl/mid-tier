from django.test import TestCase

from preprocess.utils import MockInitializer
from events.utils import CachedCategoryTree

class InitializerTest(TestCase):
    fixtures = ['categories.json', 'auth.json', 'default_behavior.json', 'places']

    def setUp(self):
        self.n = 5
        MockInitializer(self.n).run()

    def test_load_db(self):
        ctree = CachedCategoryTree()
        for cc in ctree.all_concrete():
            self.assertEqual(self.n, cc.events_concrete.all().count())