from django.test import TestCase
from pundit.base import BaseRule
from pundit.arbiter import Arbiter
from importer.models import ExternalCategory
from events.models import Event, Category, Source
from importer.models import ExternalCategory
from pundit.base import BaseRule
from pundit.classification_rules import SourceRule, SourceCategoryRule


class RulesTest(TestCase):
    """
    """
    fixtures = ['events', 'categories', 'sources', 'external_categories.json']
    
    def test_classify(self):
        """
        """
        base_rule = BaseRule()
        self.assertRaises(NotImplementedError, base_rule.classify, None)

    def test_SourceRule(self):
        """
        """
        source_rule = SourceRule()
        for event in Event.objects.all():
            # Here add an additional check for existence of the spiders
            # information in the SourceModel
            abstracts = None
            try:
                abstracts = event.categories.get()
            except:
                pass
            
            
            ext_cat_obj = ExternalCategory.objects.filter(
                source__name='fandango',
                category=event.concrete_category)[0]

            source_name = ext_cat_obj.source.name
            event_category = ([event.concrete_category], [abstracts])
            self.assertEqual(event_category,
                             source_rule.classify(event, source_name))

    def test_SourceCategoryRule(self):
        """
        """
        source_category_rule = SourceCategoryRule()
        for event in Event.objects.all():
            # Here add an additional check for existence of the spiders
            # information in the SourceCategoryModel
            abstracts = None
            try:
                abstracts = event.categories.get()
            except:
                pass

            ext_cat_obj = ExternalCategory.objects.filter(
                source__name='villagevoice',
                category=event.concrete_category)[0]

            source_name = ext_cat_obj.source.name
            xid =  ext_cat_obj.xid
            result = source_category_rule.classify(event, source_name,[xid])
            event_category = ([event.concrete_category], [])
            self.assertEqual(event_category, result)
                             
                              

class ArbiterTest(TestCase):
    """
    """

    fixtures = ['events', 'categories', 'sources', 'external_categories.json']
    
    def test_chain(self):
        """
        """
        # Broad check
        arbiter = Arbiter([SourceCategoryRule(), SourceRule()])
        for event in Event.objects.all():
            concrete, abstracts = arbiter.apply_rules(event)
            self.assertEqual(concrete, [event.concrete_category])
            # Confirm that this does not compare a list of events to a
            # Manager
            # Tests for abstracts don't work yet.
            # self.assertEqual(abstracts, event.categories)




    
            
