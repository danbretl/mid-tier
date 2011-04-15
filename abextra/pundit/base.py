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

    def classify(self, event, source, **kwargs):
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


    def get_concrete_category(self,event, spider, external_categories):
        if event == self.event:
            return self.concrete_categories
        else:
            self.classify(event, spider, external_categories)
            return self.concrete_categories

    def get_abstract_category(self, event, spider, external_categories):
        if event == self.event:
            return self.abstract_categories
        else:
            self.classify(event, spider, external_categories)
            return self.abstract_categories

    # TODO: This seems fairly useful and shouldn't belong here.
    #       This should be in some helper class
    def separate_concretes_abstracts(self, categories):
        concretes = []
        abstracts = []
        for category in categories:
            if category.category_type == 'C':
                concretes.append(category)
            elif category.category_type == 'A':
                abstracts.append(category)

        return (concretes, abstracts)
