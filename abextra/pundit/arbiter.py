"""
Module implents Arbiter
"""
from events.utils import CachedCategoryTree

class Arbiter(object):
    """
    This module is the set of rules that get applied to an event.

    Each rule has a clause, input and output.
    Rules can be chained together to form a complex tree.
    For now:
    One and only one chain in the tree will ever get applied.
    Each chain is an ordered list of rules.
    Each chain has an optional output_manipulator which can be implemented
    to massage the output for the next rule.
    """
    def __init__(self, rules):
        """
        """
        self.rules = rules
        self.cachedcategorytree = CachedCategoryTree()

    def apply_rules(self, event, source, external_categories):
        """
        This function has no side effects.
        It applies all its rules to the event object and returns raw categories
        These raw categories may need to be filtered down (using the
        concrete_category and abstract_category functions.)
        """
        raw_abstracts = []
        raw_concretes = []
        for rule in self.rules:
            concretes, abstracts = rule.classify(event, source,
                                                 external_categories=\
                                                 external_categories)

            # Special handling for event classification rules.
            # Could later put this into a special class and abstract out
            # the common theme into a BaseChain class.
            concretes = [category for category in concretes if category]
            if concretes and not raw_concretes:
                raw_concretes = concretes
            raw_abstracts.extend(abstracts)

        return (raw_concretes, raw_abstracts)

    def abstract_categories(self, event, source, ext_category_xids=None):
        return self.apply_rules(event, source, ext_category_xids)[1]

    def concrete_categories(self, event, source, ext_category_xids=None):
        categories = self.apply_rules(event, source, ext_category_xids)[0]
        return self.cachedcategorytree.deepest_category(categories)
