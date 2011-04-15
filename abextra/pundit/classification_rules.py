"""
Author: Vikas Menon
Date: Apr 12 2011
"""

from collections import defaultdict

from pundit.base import BaseRule
from events.models import Source
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
        self.concrete_dict = defaultdict(list)
        self.abstract_dict = defaultdict(list)
        #-------------------------------------
        # These variables are used during caching
        self.event = None
        self.concrete_categories = None
        self.abstract_categories = None
        #-------------------------------------
        for src in Source.objects.select_related('default_concrete_category').all():
            self.concrete_dict[src.name].append(src.default_concrete_category)
            abstracts = None
            try:
                abstracts = src.default_abstract_categories.get()
            except:
                pass
            self.abstract_dict[src.name].append(abstracts)

    def classify(self, event, source, **kwargs):
        """
        Arguments:
        -  `event`: scraped event to be classified. This includes information
                    from the scrape to allow for better classifion like spider,
                    since the event django object does not support such fields.
        """
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
        self.concrete_categories = None
        self.abstract_categories = None
        #-------------------------------------

        for ext_cat in ExternalCategory.objects.select_related('source', 'category').all():
            key = (ext_cat.source, ext_cat)
            if ext_cat.category.category_type == 'C':
                self.concrete.setdefault(key, []).append(ext_cat.category)
            elif ext_cat.category.category_type == 'A':
                self.abstract.setdefault(key, []).append(ext_cat.category)

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
        return (results_concrete,results_abstract)


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
    def __init__(self, key, model):
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
        source_dict = defaultdict(dict)

        if model:
            regex_objs = RegexCategory.objects.select_related().filter(model_type=model)
        else:
            regex_objs = RegexCategory.objects.all()

        self.default_rules = []
        self.source_rules = defaultdict(list)
        for rgx_obj in regex_objs:
            if rgx_obj.source:
                self.source_rules[rgx_obj.source].append(
                    (re.compile(rgx_obj.regex, re.IGNORECASE),
                    rgx_obj.category)
                    )
            else:
                self.default_rules.append(
                    (re.compile(rgx_obj.regex, re.IGNORECASE),
                                           rgx_obj.category)
                    )

    def classify(self, event, source, xids):
        """
        rules = self.source_rules[source] + self.null_rules
        for regex, category in rules:
            if regex.search(self.key(event,source,xids)):
              assign category
        """
        input_string = self.key(event, source, xids)
        if not input_string:
            return

        self.event = event
        self.concrete_categories = self.abstract_categories = []

        # Apply the 2 dictionaries in order or precedence:
        # TODO: see if there is any value in refactoring this.
        #----------------------------------------------------------------------

        categories = []
        for regex,category in self.source_rules[source]:
            if regex.search(input_string):
                categories.append(category)
        if categories:
            self.concrete_categories, self.abstract_categories = \
                                   self.separate_concretes_abstracts(categories)
            return
        #----------------------------------------------------------------------
        for regex, category in self.default_rules:
            if regex.search(input_string):
                categories.append(category)
        if  categories:
            self.concrete_categories, self.abstract_categories = \
                                   self.separate_concretes_abstracts(categories)

        return


class TitleRegexRule(RegexRule):
    """Applies regexes to title of an event to discover
    concrete and abstract categories"""
    def __init__(self):
        RegexRule.__init__(self, lambda e,s,x: e.title, 'TextRegex')

class DescriptionRegexRule(RegexRule):
    """Applies regexes to description"""
    def __init__(self):
        RegexRule.__init__(self, lambda e,s,x: e.description,'TextRegex')

class XIDRegexRule(RegexRule):
    """Applies regexes to  XID"""
    def __init__(self):
        xkey = lambda e,s,x: " ".join([obj.name for obj in x])
        RegexRule.__init__(self, xkey, 'XIDRegex')
