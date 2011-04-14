"""
Author: Vikas Menon
Date: Apr 11 2011
"""

class BaseRule(object):
    """
    Each rule has a clause, input and output
    For a given input, if the clause evaluates to true, the rule gets applied
    and an output is generated. 
    """

    def __init__(self):
        """
        """
        pass

    def gen_concrete_category(self,event):
        """
        """
        if event.concrete_category:
            return
        else:
            return self.classify(event)

    def gen_abstract_category(self, event):
        """
        """
        
    def classify(self, scraped_event):
        """
        Arguments:
        - `scraped_event`: This also includes outside information such as
        source of event, external categorization information, meta informatin
        about the location, etc.
        
        The rules that was applied (for debugging), the confidence measure of
        that rule etc.
        info = None
        This is a list of abstract categories and other information indicating
        abstract_info = ([None],info)
        This is a two tuple indicating 
        concrete_info = (None, info)
        return_tuple = (concrete_info, abstract_info)

        Any rule must implement this as its base class. 
        """
        raise NotImplementedError


    def concrete_category(self,event, spider, external_categories):
        if event == self.event:
            return self.concrete_categories
        else:
            self.classify(event, spider, external_categories, *args, **kwargs)
            return self.concrete_categories

    def abstract_category(self, event, spider, external_categories):
        if event == self.event:
            return self.abstract_categories
        else:
            self.classify(event, spider, external_categories, *args, **kwargs)
            return self.abstract_categories

        

        

        
