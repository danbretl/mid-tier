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

class Arbiter(object):
    """
    """

    def __init__(self, rules):
        """
        """
        self.rules = rules

    def apply_rules(self, event, source, external_category_xids):
        """
        """
        concrete_category = None
        abstract_categories = []
        for rule in self.rules:
            concrete, abstracts = rule.classify(
                event, source, external_category_xids
            )

            # Special handling for event classification rules.
            # Could later put this into a special class and abstract out
            # the common theme into a BaseChain class.
            if concrete and not concrete_category:
                concrete_category = concrete
            abstract_categories.extend(abstracts)

        return (concrete_category, abstract_categories)
