"""
Author: Vikas Menon
Last Modified: May 16th 2011
"""
from django.test import TestCase
from importer.models import ExternalCategory
from events.models import Event, Category, Source
from importer.models import ExternalCategory
from pundit.base import BaseRule
from pundit.classification_rules import SourceRule, SemanticCategoryMatchRule, \
     SourceCategoryRule, DescriptionRegexRule, TitleRegexRule, XIDRegexRule
from pundit.arbiter import Arbiter

class RulesTest(TestCase):
    """
    Test Source and Source Category Rule. Both of these rules are currently
    employed in production.
    """
    fixtures = ['events', 'categories', 'sources', 'external_categories']

    def test_classify(self):
        """
        Test to ensure BaseRule cannot be instantiated without implementing
        abstract method classify.
        """
        self.assertRaises(TypeError, BaseRule)

    def test_source_rule(self):
        """
        Ensure SourceRule works as expected on Fandango.
        Invariant: All events imported from Fandango are movies.
        """
        source_rule = SourceRule()
        # MAke this test more comprehensive with more fandango objects.
        source = Source.objects.get(name='fandango')
        event_category = ([Category.objects.get(title='Movies')], [])
        for event in Event.objects.filter(id__in=[2]):
            # Here add an additional check for existence of the spiders
            # information in the SourceModel
            self.assertEqual(event_category,
                             source_rule.classify(event, source))

    def test_source_category_rule(self):
        """
        Ensure SourceCategoryRule works as expected with Villagevoice scrapes.
        """
        source_category_rule = SourceCategoryRule()
        for event in Event.objects.all():
            ext_cat_obj = ExternalCategory.objects.filter(
                source__name='villagevoice',
                concrete_category = event.concrete_category)[0]

            source = ext_cat_obj.source
            result = source_category_rule.classify(event, source, \
                external_categories=[ext_cat_obj])
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
        Test a simple chain in production. The more complex rules are arranged
        at the start and the simpler rules are last.
        We should consider a final stop rule that on failure assigns
        unclassified
        """
        # Broad check
        arbiter = Arbiter([
            SourceCategoryRule(),
            SourceRule()
        ])
        source1 = Source.objects.get(name='villagevoice')
        source2 = Source.objects.get(name='fandango')
        movie_category = Category.objects.get(title='Movies')
        for event in Event.objects.all():
            ext_cat_objs = ExternalCategory.objects.filter(
                concrete_category=event.concrete_category)
            for ext_cat_obj in ext_cat_objs:
                concrete = arbiter.apply_rules(event, source1, [ext_cat_obj])[0]
                if concrete:
                    break

            self.assertEqual(concrete, [event.concrete_category])
            # Tests for abstracts don't work yet.
            # self.assertEqual(abstracts, event.categories)
            concrete = arbiter.apply_rules(event, source2, [])[0]
            self.assertEqual(concrete, [movie_category])


    def test_concrete_filters(self):
        """
        Stub
        """
        arbiter = Arbiter([
            SourceCategoryRule(),
            SourceRule()
        ])
        source = Source.objects.get(name='villagevoice')
        xid_list = ['1134089', '1134052', '1134052']
        xids = ExternalCategory.objects.filter(xid__in=xid_list)
        for event in Event.objects.filter(concrete_category__id=28):
            concrete = arbiter.concrete_categories(event, source, xids)
            self.assertEqual(event.concrete_category, concrete)


class RegexRulesTest(TestCase):
    """
    Tests that need to be performed
    - Test TitleRegexRule
    - Test DescriptionRegexRule
    - Test XIDRegexRule
    """
    fixtures = ['events', 'categories', 'sources',
                'external_categories', 'regexcategories']

    def test_description_regex_rule(self):
        """
        stub
        """
        event = Event.objects.get(id=2)
        source = Source.objects.get(name='villagevoice')
        ext = ExternalCategory.objects.get(id=108)
        dregexrule = DescriptionRegexRule()
        drr_category = dregexrule.get_concrete_category(event, source, ext)[0]
        self.assertEqual(event.concrete_category, drr_category)

    def test_title_regex_rule(self):
        """
        Stub
        """
        event = Event.objects.get(id=2)
        source = Source.objects.get(name='villagevoice')
        ext = ExternalCategory.objects.get(id=108)
        tregexrule = TitleRegexRule()
        trr_category = tregexrule.get_concrete_category(event, source, ext)[0]
        self.assertEqual(event.concrete_category, trr_category)

    def test_xid_regex_rule(self):
        """
        Stub
        """
        event = Event.objects.get(id=2)
        source = Source.objects.get(name='villagevoice')
        ext = ExternalCategory.objects.get(id=108)
        xregexrule = XIDRegexRule()
        xrr_category = xregexrule.get_concrete_category(event, source, [ext])[0]
        self.assertEqual(event.concrete_category, xrr_category)

    def test_semantic_match_rule(self):
        """
        Stub
        """
        event = Event.objects.get(id=2)
        source = Source.objects.get(name='villagevoice')
        category = Category.objects.get(title='Adventure')
        ext = ExternalCategory.objects.get(id=1080)
        semantic_rule = SemanticCategoryMatchRule()
        self.assertEqual([category], semantic_rule.get_abstract_category(event,
                                                                       source,
                                                                       [ext]))
