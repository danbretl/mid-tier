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
