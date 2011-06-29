from django.test import TestCase
from importer.models import ExternalCategory
from events.models import Event, Category, Source
from places.models import Place
from importer.models import ExternalCategory
from pundit.base import BaseRule
from pundit.classification_rules import SourceRule, SemanticCategoryMatchRule,\
     SourceCategoryRule, DescriptionRegexRule, TitleRegexRule, XIDRegexRule,\
     LocationRule

from pundit.arbiter import Arbiter

class RulesTest(TestCase):
    """
    """
    fixtures = ['events', 'categories', 'sources', 'external_categories.json']

    def test_classify(self):
        """
        """
        base_rule = BaseRule()
        self.assertRaises(NotImplementedError, base_rule.classify, None, None)

    def test_SourceRule(self):
        """
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

        self.assertEqual(event_category, source_rule.classify(event, source))

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
                concrete_category=event.concrete_category)[0]

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
                concrete, abstracts = arbiter.apply_rules(event,
                                                          source1,
                                                          [ext_cat_obj])
                if concrete:
                    break

            self.assertEqual(concrete, [event.concrete_category])
            # Confirm that this does not compare a list of events to a
            # Manager
            # Tests for abstracts don't work yet.
            # self.assertEqual(abstracts, event.categories)
            source = Source.objects.get(id=2)
            concrete, abstracts = arbiter.apply_rules(event,
                                                       source2,
                                                       [])
            self.assertEqual(concrete, [movie_category])


    def test_concrete_filters(self):
        arbiter = Arbiter([
            SourceCategoryRule(),
            SourceRule()
        ])
        source = Source.objects.get(name='villagevoice')
        xid_list = ['1134089', '1134052', '1134052']
        xids = ExternalCategory.objects.filter(xid__in=xid_list)
        for event in Event.objects.filter(concrete_category__id=28):
            concrete = arbiter.concrete_categories(event, source, xids)
            self.assertEqual(event.concrete_category,concrete)


class RegexRulesTest(TestCase):
    """
    Tests that need to be performed
    - Test TitleRegexRule
    - Test DescriptionRegexRule
    - Test XIDRegexRule
    """
    fixtures = ['events', 'categories', 'sources',
                'external_categories', 'regexcategories']

    def test_DescriptionRegexRules(self):
        """
        """
        event = Event.objects.get(id=2)
        source = Source.objects.get(name='villagevoice')
        ext = ExternalCategory.objects.get(id=108)
        dregexrule = DescriptionRegexRule()
        drr_category = dregexrule.get_concrete_category(event, source, ext)[0]
        self.assertEqual(event.concrete_category, drr_category)

    def test_TitleRegexRules(self):
        """
        """
        event = Event.objects.get(id=2)
        source = Source.objects.get(name='villagevoice')
        ext = ExternalCategory.objects.get(id=108)
        tregexrule = TitleRegexRule()
        trr_category = tregexrule.get_concrete_category(event, source, ext)[0]
        self.assertEqual(event.concrete_category, trr_category)

    def test_XIDRegexRule(self):
        event = Event.objects.get(id=2)
        source = Source.objects.get(name='villagevoice')
        ext = ExternalCategory.objects.get(id=108)
        xregexrule = XIDRegexRule()
        xrr_category = xregexrule.get_concrete_category(event, source, [ext])[0]
        self.assertEqual(event.concrete_category, xrr_category)

    def test_SemanticMatchRule(self):
        event = Event.objects.get(id=2)
        source = Source.objects.get(name='villagevoice')
        category = Category.objects.get(title='Adventure')
        ext = ExternalCategory.objects.get(id=1080)
        semantic_rule = SemanticCategoryMatchRule()
        self.assertEqual([category], semantic_rule.get_abstract_category(event,
                                                                       source,
                                                                       [ext]))

class LocationRuleTest(TestCase):
    fixtures = ['events', 'categories', 'sources',
                'external_categories', 'regexcategories', 'places']

    def test_locationrule(self):
        event = Event.objects.all()[0]
        source = Source.objects.get(name='villagevoice')
        place = Place.objects.get(id=336)
        expected_result = ([place.concrete_category], set(place.abstract_categories.all()))
        location_rule = LocationRule()
        calculated_result = (location_rule.get_concrete_category(event, None, []),\
                            set(location_rule.get_abstract_category(event, None, [])))
        self.assertEqual(expected_result, calculated_result)

