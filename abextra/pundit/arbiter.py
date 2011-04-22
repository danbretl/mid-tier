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
from importer.models import ExternalCategory
from events.utils import CachedCategoryTree

class Arbiter(object):
    """
    """

    def __init__(self, rules):
        """
        """
        self.rules = rules
        self.event = None
        self.raw_concretes = None
        self.raw_abstracts = None
        self.filtered_concrete = None
        self.filtered_abstract = None
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
            concretes, abstracts = rule.classify(event, source, external_categories=external_categories)

            # Special handling for event classification rules.
            # Could later put this into a special class and abstract out
            # the common theme into a BaseChain class.
            if concretes and not raw_concretes:
                raw_concretes = concretes
            raw_abstracts.extend(abstracts)

        return (raw_concretes, raw_abstracts)

    def _apply_filters(self, event, source, ext_categories):
        """
        This function filters down the  concrete categories and returns
        """
        if not event:
            return
        if self.event == event:
            return

        self.event = event
        raw_concretes, raw_abstracts = self.apply_rules(event,
                                                        source,
                                                        ext_categories)
        #clean concrete and abstracts here
        self.filtered_abstract = raw_abstracts
        self.filtered_concrete = self.cachedcategorytree \
            .deepest_category(raw_concretes) if raw_concretes else []

    def abstract_categories(self, event, source, ext_category_xids=None):
        self._apply_filters(event, source, ext_category_xids)
        return self.filtered_abstract

    def concrete_categories(self, event, source, ext_category_xids=None):
        self._apply_filters(event, source, ext_category_xids)
        return self.filtered_concrete
