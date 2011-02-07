# import random
# 
# from events import models as ems
# class EventureInitializer(object):
#     """factory class for initialization of eventure app"""
# 
#     def __init__(self, n_events=100, categories=None, cross_categorization=4):
#         super(EventureInitializer, self).__init__()
#         self.n_events = n_events
# 
#         # fetch necessary categories
#         c_base = ems.Category.objects
#         self.categories = c_base.filter(id__in=categories) if categories else c_base.all()
# 
#     def run(self):
#         pass

from core.utils import Bunch
CategoryNode = Bunch

for id, category in categories_by_id.iteritems():
    # assign parent from the cache hash
    parent_id = category.parent_id
    category.parent = categories_by_id[parent_id] if parent_id else None

    # assign children
    category.children = category_by_id

def _category_tree():
    categories_by_id = dict((c.id, c) for c in Category.objects.all())
    for id, category in categories_by_id.iteritems():
        parent = categories_by_id.get(category.parent_id)
        if parent:
            category.parent = parent
    return categories_by_id

def _concrete_category_tree():
    categories_by_id = _category_tree()

