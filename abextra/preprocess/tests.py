from django.test import TestCase
from django.template.defaultfilters import slugify

from preprocess.utils import MockInitializer
from events.utils import CachedCategoryTree

class InitializerTest(TestCase):
    fixtures = ['auth', 'categories', 'places']

    def setUp(self):
        self.n = 5
        MockInitializer(self.n).run()

    def test_load_db(self):
        ctree = CachedCategoryTree()
        for cc in ctree.children(ctree.concrete_node):
            self.assertEqual(self.n, cc.events_concrete.all().count())
