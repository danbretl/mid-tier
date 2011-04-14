from django.test import TestCase
from importer.models import ExternalCategory
from events.models import Event, Category, Source
from importer.models import ExternalCategory
from pundit.base import BaseRule
from pundit.classification_rules import SourceRule, SourceCategoryRule
from pundit.arbiter import Arbiter

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

            source = ext_cat_obj.source
            xid =  ext_cat_obj.xid
            result = source_category_rule.classify(event, source, [xid])
            event_category = ([event.concrete_category], [])
            self.assertEqual(event_category, result)


class ArbiterTest(TestCase):
    """
    Test cases:
    -  If an external category object has no category assigned, the source
       category rule should not get applied.
    """

    fixtures = ['events', 'categories', 'sources', 'external_categories']

    def test_chain(self):
        """
        """
        # Broad check
        arbiter = Arbiter([
            SourceCategoryRule(),
            SourceRule()
        ])
        source = 'villagevoice'
        for event in Event.objects.all():
            ext_cat_objs = ExternalCategory.objects.filter(category=event.concrete_category)
            for ext_cat_obj in ext_cat_objs:
                concrete, abstracts = arbiter.apply_rules(event,
                                                          source,
                                                          [ext_cat_obj.xid])
                if concrete:
                    break

            self.assertEqual(concrete, [event.concrete_category])
            # Confirm that this does not compare a list of events to a
            # Manager
            # Tests for abstracts don't work yet.
            # self.assertEqual(abstracts, event.categories)

    def test_concrete_filters(self):
        arbiter = Arbiter([
            SourceCategoryRule(),
            SourceRule()
        ])
        source = 'villagevoice'
        xids = ['1134089', '1134052', '1134052']
        for event in Event.objects.filter(concrete_category__id=28):
            concrete = arbiter.concrete_categories(event, source, xids)
            self.assertEqual(event.concrete_category,concrete)
