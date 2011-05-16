"""
Author: Vikas Menon
Date: Apr 11 2011
"""
from abc import ABCMeta, abstractmethod

class BaseRule:
    """
    Each rule has a clause, input and output
    For a given input, if the clause evaluates to true, the rule gets applied
    and an output is generated.
    """
    __metaclass__ = ABCMeta

    def __init__(self):
        """
        Each Rule must define its own init. Each init must contain the following
        three member:
        1) self.concrete_categories
        2) self.abstract_categories
        3) self.event
        """
        self.abstract_categories = self.concrete_categories = self.event = None
        raise NotImplementedError

    @abstractmethod
    def classify(self, event, source, external_categories, **kwargs):
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


    def get_concrete_category(self, event, spider, external_categories):
        """
        Given input event, spider (or the source) and external_categories
        returns a list of concrete  categories
        """
        if event == self.event:
            return self.concrete_categories
        else:
            self.classify(event, spider, external_categories)
            return self.concrete_categories

    def get_abstract_category(self, event, spider, external_categories):
        """
        Given input event, spider (or the source) and external_categories
        returns a list of abstract categories
        """
        if event == self.event:
            return self.abstract_categories
        else:
            self.classify(event, spider, external_categories)
            return self.abstract_categories
