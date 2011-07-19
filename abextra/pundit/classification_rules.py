"""
Author: Vikas Menon
Date: Apr 12 2011
"""

from collections import defaultdict

from pundit.base import BaseRule
from events.models import Source, Category
from importer.models import ExternalCategory, RegexCategory
import re

### NOTES ###
"""
What the SourceCategory model is going to look like:
source   xids    concrete    abstract
string   string  ForeignKey  ManyToMany

TODO:
Set up new SourceCategory table that fits with concrete and abstract
Finish DirectMappingRule (abstract list setup, NULL handling)
Write test cases

Write Regex!
"""


class DirectMappingRule(BaseRule):
    def __init__(self, rule_table, orderings):
        """example ordering: (('Source', 'XID'), ('XID'))"""
        mapping_dict = defaultdict(dict)
        for row in rule_table.objects.all():
            for ordering in orderings:
                thiskey = tuple([row.getattr(o) for o in ordering])

                # if any of them are null, this rule is too specific
                # TODO: I do not know if NULL translates to None
                if None in thiskey:
                    continue
                mapping_dict[ordering][thiskey] = (row.concrete, row.abstracts)

    def classify(self, event, source, xids):
        # apply all rules to it in order
        concrete, abstract = None, []

        def get_event_field(name):
            """
            given the name of a field within an event ('title',
            'description') or alternatively 'source' or 'xids', return
            requested information for use in direct map
            """
            return (source if name == 'source' else
                    (xids if name == 'xids' else
                     event.getattr(name)))
        for ordering, mapping in self.mapping_dict.iteritems():
            # get this key of this event
            thiskey = tuple([get_event_field(o) for o in ordering])
            result = mapping.get(thiskey)

            if result:
                # the mapping will be a tuple of concrete and abstracts
                # suggestions
                this_concrete, this_abstract = result
                # check that each are not null, and that we're not overwriting a
                # better concrete
                # TODO: NULL might be different from None. Check this!
                if not concrete and this_concrete:
                    concrete = this_concrete
                if this_abstract:
                    abstract.extend(this_abstract)


class SourceCategoryMapRule(DirectMappingRule):
    def __init__(self):
        orderings = (('source', 'xids'), ('source'))
        DirectMappingRule.__init__(self, SourceCategory, orderings)


class SourceRule(BaseRule):
    """
    TODO: the logic of this class should now be deprecated- remove it soon!
    """

    def __init__(self):
        """
        """
        self.concrete_dict = {}
        self.abstract_dict = {}
        #-------------------------------------
        # These variables are used during caching
        self.event = None
        self.concrete_categories = None
        self.abstract_categories = None
        #-------------------------------------
        for src in Source.objects.select_related('default_concrete_category').all():
            self.concrete_dict.setdefault(src, []).append(src.default_concrete_category)
            abstracts = []
            try:
                abstracts = src.default_abstract_categories.all()
            except:
                pass

            self.abstract_dict.setdefault(src,[]).extend(abstracts)

    def classify(self, event, source, **kwargs):
        """
        Arguments:
        -  `event`: scraped event to be classified. This includes information
                    from the scrape to allow for better classifion like spider,
                    since the event django object does not support such fields.
        """
        # if not kwargs.get('external_categories'):
        #     import ipdb; ipdb.set_trace()
        results_concrete = []
        results_abstract = []
        if source:
            results_concrete = self.concrete_dict[source]
            results_abstract = self.abstract_dict[source]

        #------------------------------------------
        #Caching results
        self.event = event
        self.concrete_categories = results_concrete
        self.abstract_categories = results_abstract
        #------------------------------------------
        return (results_concrete,results_abstract)


class SourceCategoryRule(BaseRule):
    """
    TODO: remove this too!
    """

    def __init__(self):
        """
        """
        self.concrete = {}
        self.abstract = {}
        #-------------------------------------
        # These variables are used during caching
        self.event = None
        self.concrete_categories = []
        self.abstract_categories = []
        #-------------------------------------

        for ext_cat in ExternalCategory.objects.select_related('source', 'conrete_category', 'abstract_categories').all():
            key = (ext_cat.source, ext_cat)
            self.concrete.setdefault(key, []).append(ext_cat.concrete_category)
            self.abstract.setdefault(key, []).extend(ext_cat.abstract_categories.all())

    def classify(self, event, source, **kwargs):
        external_categories = kwargs['external_categories']
        results_concrete = []
        results_abstract = []
        if source and external_categories:
            # Get all possible categories.
            for ext_cat in external_categories:
                key = (source, ext_cat)
                results_concrete += self.concrete.get(key, [])
                results_abstract += self.abstract.get(key, [])
        #------------------------------------------
        #Caching results
        self.event = event
        self.concrete_categories = results_concrete
        self.abstract_categories = results_abstract
        #------------------------------------------
        return ([r for r in results_concrete if r], results_abstract)


"""
TODO:

REGEX and SOURCEREGEX rules work on the same table importer_regexcategory
regex is a more general rule that gets applied to all sources if sourceregex
fails when .
source
"""

class RegexRule(BaseRule):
    """
    Use a regular expression to map the external category text to internal
    categories
    """
    def __init__(self, key, model, regex_objects=None):
        """
        # note: regexes are compiled here- they are not strings
        self.source_rules = defaultdict(list) # built from a table
        self.null_rules = [] # from items in table with source NULL

        for row in model:
           key(row) -> category

        each model is of the form:
        regular_expression

        We basically build 2 different types of dictionaries;
        In order of precedence they are:
        1) source_rules   -> When we have both Source specified
        2) default_rules  -> When no source is specified.
        """
        self.event = None
        self.concrete_categories = None
        self.abstract_categories = None
        self.key = key
        if not regex_objects:
            if model:
                regex_objs = RegexCategory.objects.select_related().filter(model_type=model)
            else:
                regex_objs = RegexCategory.objects.all()
        else:
            regex_objs = regex_objects

        self.default_rules = []
        total_count = fail_count = 0

        # This is O(n^2) there should be a better way of doing this.
        # FIXME: Improve time complexity if this is too slow.
        rules_bunch = defaultdict(set)
        for regex_big in regex_objs:
            for regex_small in regex_objs:
                if regex_small.regex == regex_big.regex:
                    continue
                if regex_small.regex in regex_big.regex:
                    rules_bunch[regex_big].add(regex_small.category)

        for rgx_obj in regex_objs:
            total_count +=1
            try:
                self.default_rules.append((re.compile(rgx_obj.regex,
                                                      re.IGNORECASE),
                                           rgx_obj.category,
                                           rules_bunch[rgx_obj]))
            except:
                #Fails for some badly coded categories
                # FIXME: error logging please!
                fail_count += 1

    def classify(self, event, source, external_categories):
        """
        rules = self.source_rules[source] + self.null_rules
        for regex, category in rules:
            if regex.search(self.key(event,source,external_categories)):
              assign category
        """
        input_string = self.key(event, source, external_categories)
        if not input_string:
            return

        self.event = event
        self.concrete_categories = self.abstract_categories = []
        categories = concrete_categories = abstract_categories = []
        # The ignore_cats is bunch of categories to ignore if there is a match
        # Example items tuple in the for loop would be:
        # r'eurodance', <Category: Eurodance>, set(<Category: Dance>)
        # We store Dance in the list of ignored categories and later discard the match.
        ignores_set = set()
        for regex, category, ignore_cats in self.default_rules:
            if regex.search(input_string):
                categories.append(category)
                for cat in ignore_cats:
                    ignores_set.add(cat)
        if  categories:
            concrete_categories, abstract_categories = \
                                 self.separate_concretes_abstracts([c for c in categories if c not in ignores_set])
        return (concrete_categories, abstract_categories)


class TitleRegexRule(RegexRule):
    """Applies regexes to title of an event to discover
    concrete and abstract categories"""
    def __init__(self):
        RegexRule.__init__(self, lambda e,s,x: e.title, 'TitleRegex')

class DescriptionRegexRule(RegexRule):
    """Applies regexes to description"""
    def __init__(self):
        RegexRule.__init__(self, lambda e,s,x: e.description,'TextRegex')

class ArtistRegexRule(RegexRule):
    """Searches title for artists and applies abstract/concrete tags """
    def __init__(self):
        RegexRule.__init__(self, lambda e, s, x: e.title, 'ArtistRegex')

class ConditionalConcreteRule(RegexRule):
    """ """
    def __init__(self):
        RegexRule.__init__(self,
                           lambda e, s, x: e.title,
                           'ConditionalConcreteRule')

class XIDRegexRule(RegexRule):
    """Applies regexes to  XID"""
    def __init__(self):
        xkey = lambda e,s,x: " ".join([obj.name for obj in x])
        RegexRule.__init__(self, xkey, 'XIDRegex')

class SemanticCategoryMatchRule(RegexRule):
    """
    Checks if incoming categories match existing categories and assigns
    abstract and concrete categories accordingly
    Note: Currently used only for abstract categorization.
    """
    def __init__(self):
        xkey = lambda e,s,x: " ".join([obj.name for obj in x])
        regex_objs = []
        # Loop over all ABSTRACT categories only.
        for category in Category.abstract.all():
            #we should get rid of any unwanted terms that could match
            # like genres or
            # Multiple matches for the same category should get more weight.
            word = category.title.lower()
            regex_obj = RegexCategory()
            regex_obj.regex = word
            regex_obj.category = category
            regex_objs.append(regex_obj)
        RegexRule.__init__(self, xkey, None, regex_objs)

class LocationRule(BaseRule):
    """
    Classify based on event location
    """
    def classify(self, event, spider, external_categories):
        results_concrete = []
        results_abstract = []
        for place in event.places:
            if place.concrete_category:
                results_concrete.append(place.concrete_category)
            raw_abs = place.abstract_categories.all()
            if raw_abs:
                results_abstract.extend(raw_abs)

        return (results_concrete, results_abstract)


class PlaceTypeRule(BaseRule):
    """
    Classify events based on place type
    """
    def classify(self, event, spider, external_categories):
        results_concrete = results_abstract = []
        for place in event.places:
            for place_type in place.place_types.all():
                if place_type.concrete_category:
                    results_concrete.append(place_type.concrete_category)
                raw_abs = place_type.abstract_categories.all()
                if raw_abs:
                    results_abstract.extend(raw_abs)

        return (results_concrete, results_abstract)

class ConditionalCategoryRule(BaseRule):
    """
    """
    def __init__(self, key=lambda e, s, x: e.title):
        self.key = key
        self.rules = defaultdict(list)
        for obj in ConditionalCategoryModel.objects.all():
            self.rules[obj.conditional_category].append(
                (re.compile(obj.regex), obj.category)
                )

    def classify(self, event, spider, external_categories):
        categories = []
        input_string = self.key(event, spider, external_categories)
        for regex, category in self.rules[event.concrete_category]:
            if regex.search(input_string):
                categories.append(category)

        if  categories:
            return self.separate_concretes_abstracts(categories)
        else:
            return ([], [])
