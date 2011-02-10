from collections import defaultdict
from events.models import Category

class CachedCategoryTree(object):
    abstract_title = 'abstract'
    concrete_title = 'concrete'

    def __init__(self, skinny=False):
        # prepare the initial db queryset
        category_qs = Category.objects
        if skinny:
            category_qs = category_qs.defer('icon', 'icon_height', 'icon_width')
            category_qs = category_qs.defer('is_associative', 'association_coefficient')
        category_qs = category_qs.all()

        # hash categories by id
        self._categories_by_id = dict( (c.id, c) for c in category_qs)

        # process parents efficiently in memory
        for c in self._categories_by_id.itervalues():
            c.parent = self._categories_by_id.get(c.parent_id)

        # hash categories by title
        self._categories_by_title = dict(
            (c.title.lower(), c) for c in self._categories_by_id.itervalues()
        )

        # build directed graph
        graph = defaultdict(lambda: [])
        for c in self._categories_by_id.itervalues():
            if c.parent: graph[c.parent].append(c)
        self._graph = graph

        # memoizers
        self._abstracts = self._concretes = None

    def category_by_id(self, id):
        return self._categories_by_id[id]
    def category_by_title(self, title):
        return self._categories_by_title[title.lower()]

    # FIXME simplify recursion
    # FIXME preemptive recursion with caching for better consequent requests
    def _children_recursive(self, category, l):
        for c in self._graph[category]:
            l.append(c)
            self._children_recursive(c, l)
        return l
    def children_recursive(self, category):
        return self._children_recursive(category, [])
    def children(self, category):
        return self._graph[category]

    @property
    def abstracts(self):
        if not self._abstracts:
            c = self.category_by_title(self.abstract_title)
            self._abstracts = self.children_recursive(c)
        return self._abstracts

    @property
    def concretes(self):
        if not self._concretes:
            c = self.category_by_title(self.concrete_title)
            self._concretes = self.children_recursive(c)
        return self._concretes