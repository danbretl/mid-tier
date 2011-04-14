"""
Author: Vikas Menon
Date: Apr 12 2011
"""

from collections import defaultdict

from pundit.base import BaseRule
from events.models import Source
from importer.models import ExternalCategory

class SourceRule(BaseRule):
    """
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
        for src in Source.objects.all():
            self.concrete_dict[src.name].append(src.default_concrete_category)
            abstracts = None
            try:
                abstracts = src.default_abstract_categories.get()
            except:
                pass
            self.abstract_dict[src.name].append(abstracts)

    def classify(self, event, spider, xids):
        """
        Arguments:
        -  `event`: scraped event to be classified. This includes information
                    from the scrape to allow for better classifion like spider,
                    since the event django object does not support such fields.
        
        """
        results_concrete = []
        results_abstract = []
        if spider:
            results_concrete = self.concrete_dict[spider]
            results_abstract = self.abstract_dict[spider]

        #------------------------------------------
        #Caching results
        self.event = event
        self.concrete_categories = results_concrete
        self.abstract_categories = results_abstract
        #------------------------------------------
        return (results_concrete,results_abstract)


class SourceCategoryRule(BaseRule):
    """
    """

    def __init__(self):
        """
        """
        self.concrete = defaultdict(list)
        self.abstract = defaultdict(list)
        #-------------------------------------
        # These variables are used during caching
        self.event = None
        self.concrete_categories = None
        self.abstract_categories = None
        #-------------------------------------

        for ext_cat in ExternalCategory.objects.all():
            name_xid = (ext_cat.source.name, ext_cat.xid)
            if ext_cat.category.category_type == 'C':
                if ext_cat.category:
                    self.concrete[name_xid].append(ext_cat.category)
            elif ext_cat.category.category_type == 'A':
                if ext_cat.category:
                    self.abstract[name_xid].append(ext_cat.category)
            
    def classify(self, event, spider, external_categories, *args, **kwargs):
        """
        """
        results_concrete = []
        results_abstract = []
        if spider and external_categories:
            # Get all possible categories. 
            for category in external_categories:
                results_concrete += self.concrete[(spider, category)]
                results_abstract += self.abstract[(spider, category)]
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
    def __init__(self, model, key):
        """
        # note: regexes are compiled here- they are not strings
        
        self.source_rules = defaultdict(list) # built from a table
        self.null_rules = [] # from items in table with source NULL

        for row in model:
           key(row) -> category

        """
        
        

    
    def classify(self, event, source, xids):
        """
        rules = self.source_rules[source] + self.null_rules
        for regex, category in rules:
            if regex.search(self.key(event,source,xids)):
              assign category
        """

class TitleRegexRule(RegexRule):
    """Applies regexes to title of an event to discover
    concrete and abstract categories"""
    def __init__(self):
        RegexRule.__init__(self, TextRegex, lambda e,s,x: e.title)

class DescriptionRegexRule(RegexRule):
    """Applies regexes to description"""
    def __init__(self):
        RegexRule.__init__(self, TextRegex, lambda e,s,x: e.description)

class XIDRegexRule(RegexRule):
    """Applies regexes to  XID"""
    def __init__(self):
        RegexRule.__init__(self, XIDRegex, lambda e,s,x: x)
        
        
        


        
        
    
                
                
                
        
        
        

        
        

    
        
        
        
