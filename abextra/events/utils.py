from collections import defaultdict, deque
from django.template.defaultfilters import slugify
from events.models import Category

class CachedCategoryTree(object):
    def __init__(self, skinny=False):
        # prepare the initial db queryset
        category_qs = Category.objects
        if skinny:
            category_qs = category_qs.defer('icon', 'icon_height', 'icon_width')
            category_qs = category_qs.defer('is_associative', 'association_coefficient')
        category_qs = category_qs.all()

        # hash categories by id
        self._categories_by_id = dict((c.id, c) for c in category_qs)

        # process parents efficiently in memory
        for c in self._categories_by_id.itervalues():
            c.parent = self._categories_by_id.get(c.parent_id)

        # hash categories by slug
        self._categories_by_slug = dict(
            (c.slug, c) for c in self._categories_by_id.itervalues()
        )
        self.abstract_node = self._categories_by_slug['abstract']
        self.concrete_node = self._categories_by_slug['concrete']

        # build directed graph
        graph = defaultdict(lambda: [])
        for c in self._categories_by_id.itervalues():
            if c.parent: graph[c.parent].append(c)
        self._graph = graph

        # memoizers
        self._abstracts = self._concretes = None
        self._bfs_concretes = None

    def get(self, **kwargs):
        id = kwargs.get('id')
        if id:
            return self._categories_by_id[id]
        slug = kwargs.get('slug')
        if slug:
            return self._categories_by_slug[slug]
        title = kwargs.get('title')
        if title:
            return self._categories_by_slug[slugify(title)]

    # FIXME simplify recursion
    # FIXME preemptive recursion with caching for better consequent requests
    def _children_recursive(self, category, l):
        for c in self._graph[category]:
            l.append(c)
            self._children_recursive(c, l)
        return l
    def children_recursive(self, category):
        return self._children_recursive(category, [])

    def _leaves(self, category, l):
        for c in self._graph[category]:
            if not self.children(c): l.append(c)
            self._leaves(c, l)
        return l

    def leaves(self, category):
        return self._leaves(category, [])

    def children(self, category):
        return self._graph[category]

    def surface_parent(self, category):
        if not category.parent: return None
        return self.surface_parent(category.parent) if category.parent.parent else category

    def _parents(self, category, l):
        parent = category.parent
        if parent.parent:
            l.append(parent)
            self._parents(parent, l)
        return l
    def parents(self, category):
        return self._parents(category, [])

    @property
    def abstracts(self):
        if not self._abstracts:
            self._abstracts = self.children_recursive(self.abstract_node)
        return self._abstracts

    @property
    def concretes(self):
        if not self._concretes:
            self._concretes = self.children_recursive(self.concrete_node)
        return self._concretes

    def bfs(self, start, with_parent=False):
        queue, enqueued = deque([(None, start)]), set([start])
        while queue:
            parent, n = queue.popleft()
            yield (parent, n) if with_parent else n
            new = set(self._graph[n]) - enqueued
            enqueued |= new
            queue.extend([(n, child) for child in new])

    def deepest_category(self, categories):
        if not self._bfs_concretes:
            self._bfs_concretes = dict(
                (c, i) for i, c in enumerate(self.bfs(self.concrete_node))
            )
        return max(categories, key=lambda c: self._bfs_concretes[c])