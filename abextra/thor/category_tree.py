"""
This is the tree used by all machine learning algorithms.
"""
import user_behavior

from events.utils import CachedCategoryTree

class CategoryTree:
    """
    The category tree is the basis for the random tree walk algorithm
    implemented in ml for the first version of Kwiqet's Alpha release.
    It is a recursively defined as 'A CategoryTree consists of 0 or more
    CategoryTree'. The init is recursive to demonstrate the datastructure.

    Note: This datastructure is especially neccessary to understand the bottom
    and top-down recursion methods of this class. Both of these are heavily used
    methods in the random tree walk algorithm.
    """
    def __init__(self, uid, category=None, parent=None, ctree=None, eaa=None,
                 dictionary=None, behavior_db=user_behavior.DJANGO_DB):
        """
        A Tree for a user is represented recursively as a collection of trees,
        Each gtree is for a specific user.
        The name of a tree node is the category name otherwise defaults to ROOT
        the value is calculated from the persisted representation of the tree
        much the user likes this, and optionally children
        """
        self.parent = parent
        self.children = []

        if not ctree:
            ctree = CachedCategoryTree()

        if eaa == None:
            # get from DB (whether Django or dictionary)
            eaa = behavior_db.gvix_dict(uid)

        if category:
            self.children = [CategoryTree(uid, x, self, ctree, eaa)
                             for x in ctree.children(category)]
            self.category = category
            self.title = category.title
        else:
            self.children = [CategoryTree(uid, x, self, ctree, eaa)
                             for x in  ctree.children(ctree.concrete_node)]
            self.category = ctree.concrete_node
            self.title = ctree.concrete_node.title

        if dictionary:
            self.dictionary = dictionary
        else:
            self.dictionary = {}

        score = eaa.get(self.category.id)
        if score:
            self.score = score
        else:
            self.score = ((0, 0, 0, 0))


    def get_all_category_scores_dictionary(self, keys):
        """
        Input:  List of keys
        Output: Flat list of (Categories,[values])
        Return scores for keys for all Subtrees below it.
        """
        if self.get_parent():
            list = [(self.category, [self.dictionary[key] for key in keys])]
        else:
            list = []
        list += [b for a in [tree.get_all_category_scores_dictionary(keys) for tree in self.children] for b in a]
        return list



    def get_parent(self):
        """
        Return category parent
        """
        return self.parent

    def get_children(self):
        """
        Return a list of child SimpleTree objects
        """
        return self.children

    def __repr__(self):
        """
        Used primarily for testing.
        string representation in nested parentheses
        """
        ret = "'" + self.category.__repr__() + "'" + "=" + str(self.score)

        if len(self.children) > 0:
            ret += "(" + ",".join([c.__repr__() for c in self.children]) + ")"
        return ret

    def insert_key_value(self, key, value):
        """
        Insert key value into category DB
        """
        self.dictionary[key] = value

    def get_key_value(self, key):
        """
        Return value for key if found, else, return None.
        """
        return self.dictionary.get(key)

    def print_dictionary_key_values(self):
        """
        Used primarily for testing and debugging.
        Print the Category Tree as a dictionary recursively.
        """
        print self.title
        for key, value in self.dictionary.iteritems():
            print key, ":", value
        for tree in self.children:
            tree.print_dictionary_key_values()

    def subtree_score(self, inkey="score"):
        """
        Returns the sum of inkey scores for a CategoryTree and all its children.
        """
        return self.get_key_value(inkey) + \
               sum([tree.subtree_score(inkey) for tree in self.get_children()])

    #ToDo: Create a more general recursion which is capable of returning values
    #without requiring storage of values in the dictionary.
    def top_down_recursion(self, function, dictionary):
        """
        This applies function recursively to the tree in a top-down manner.
        The function is not expected to return a value. Any values generated
        must be stored in the dictionary.
        """
        function(self, **dictionary)

        for tree in self.children:
            tree.top_down_recursion(function, dictionary)

    def bottom_up_recursion(self, function, dictionary):
        """
        This applies function recursively to the tree in a bottom up manner.
        The function is not expected to return a value. Any values generated
        must be stored in the dictionary.
        """
        for tree in self.children:
            tree.bottom_up_recursion(function, dictionary)

        function(self, **dictionary)
