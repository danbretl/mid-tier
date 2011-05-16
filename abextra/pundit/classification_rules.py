"""
Author: Vikas Menon
Date: Apr 12 2011
"""

from collections import defaultdict

from pundit.base import BaseRule
from events.models import Source, Category
from events.utils import separate_concretes_abstracts
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
"""

class DirectMappingRule(BaseRule):
    """
    """
    def __init__(self, rule_table, orderings):
        """
        example ordering: (('Source', 'XID'), ('XID'))
        """
        self.mapping_dict = defaultdict(dict)
        for row in rule_table.objects.all():
            for ordering in orderings:
                thiskey = tuple([row.getattr(o) for o in ordering])

                # if any of them are null, this rule is too specific
                # TODO: I do not know if NULL translates to None
                if None in thiskey:
                    continue
                self.mapping_dict[ordering][thiskey] = (row.concrete,
                                                        row.abstracts)

    def classify(self, event, source, xids):
        """
        stub
        """
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
    """
    Stub
    """
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
        field = 'default_concrete_category'
        for src in Source.objects.select_related(field).all():
            default_concrete = src.default_concrete_category
            self.concrete_dict.setdefault(src, []).append(default_concrete)
            abstracts = []
            try:
                abstracts = src.default_abstract_categories.all()
            except:
                pass

            self.abstract_dict.setdefault(src, []).extend(abstracts)

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
        return (results_concrete, results_abstract)


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
        fields = 'source', 'conrete_category', 'abstract_categories'
        for ext_cat in ExternalCategory.objects.select_related(*fields).all():
            key = (ext_cat.source, ext_cat)
            self.concrete.setdefault(key, []).append(ext_cat.concrete_category)
            abstracts = ext_cat.abstract_categories.all()
            self.abstract.setdefault(key, []).extend(abstracts)

    def classify(self, event, source, **kwargs):
        """
        Stub
        """
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
        return (results_concrete, results_abstract)


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
                regex_objs = RegexCategory.objects.select_related().\
                             filter(model_type=model)
            else:
                regex_objs = RegexCategory.objects.all()
        else:
            regex_objs = regex_objects

        self.default_rules = []
        for rgx_obj in regex_objs:
            try:
                self.default_rules.append((re.compile(rgx_obj.regex,
                                                      re.IGNORECASE),
                                           rgx_obj.category))
            except:
                #Fails for some badly coded categories
                #FIXME: Do error logging here
                None

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
        categories = []
        for regex, category in self.default_rules:
            if regex.search(input_string):
                categories.append(category)
        if  categories:
            self.concrete_categories, self.abstract_categories = \
                                      separate_concretes_abstracts(categories)


class TitleRegexRule(RegexRule):
    """Applies regexes to title of an event to discover
    concrete and abstract categories"""
    def __init__(self):
        RegexRule.__init__(self, lambda e, s, x: e.title, 'TextRegex')


class DescriptionRegexRule(RegexRule):
    """Applies regexes to description"""
    def __init__(self):
        RegexRule.__init__(self, lambda e, s, x: e.description,'TextRegex')


class XIDRegexRule(RegexRule):
    """Applies regexes to  XID"""
    def __init__(self):
        xkey = lambda e, s, x: " ".join([obj.name for obj in x])
        RegexRule.__init__(self, xkey, 'XIDRegex')


class SemanticCategoryMatchRule(RegexRule):
    """
    Checks if incoming categories match existing categories and assigns
    abstract and concrete categories accordingly
    Note: Currently used only for abstract categorization.
    """
    def __init__(self):
        xkey = lambda e, s, x: " ".join([obj.name for obj in x])
        regex_objs = []
        # Loop over all ABSTRACT categories only.
        for category in Category.abstract.all():
            #we should get rid of any unwanted terms that could match
            # like genres or
            # Multiple matches for the same category should get more weight.
            for word in category.title.lower().split():
                regex_obj = RegexCategory()
                regex_obj.regex = word
                regex_obj.category = category
                regex_objs.append(regex_obj)
        RegexRule.__init__(self, xkey, None, regex_objs)
