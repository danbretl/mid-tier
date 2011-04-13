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

    def classify(self, event, spider=None, *args, **kwargs):
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


    def concrete_category(self,event, spider=None, *args, **kwargs):
        if event == self.event:
            return self.concrete_categories
        else:
            self.classify(event, spider, *args, **kwargs)
            return self.concrete_categories

    def abstract_category(self, event, spider=None, *args, **kwargs):
        if event == self.event:
            return self.abstract_categories
        else:
            self.classify(event, spider, *args, **kwargs)
            return self.abstract_categories


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
                self.concrete[name_xid].append(ext_cat.category)
            elif ext_cat.category.category_type == 'A':
                self.abstract[name_xid].append(ext_cat.category)
            
    def classify(self, event, spider=None, external_categories=None,
                 *args, **kwargs):
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
    
    def concrete_category(self,event, spider=None, external_categories=None,
                          *args, **kwargs):
        if event == self.event:
            return self.concrete_categories
        else:
            self.classify(event, spider, external_categories, *args, **kwargs)
            return self.concrete_categories

    def abstract_category(self, event, spider=None, external_categories=None,
                          *args, **kwargs):
        if event == self.event:
            return self.abstract_categories
        else:
            self.classify(event, spider, external_categories, *args, **kwargs)
            return self.abstract_categories

               
        
    
        
        

    
        
        
        
