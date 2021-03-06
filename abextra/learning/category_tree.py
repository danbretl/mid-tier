#from events.models import Category
#from behavior.models import EventActionAggregate
#from django.contrib.auth.models import User
#import settings
import user_behavior

from events.utils import CachedCategoryTree

class CategoryTree:
    #ToDo:
    # Efficiency Consideration: The recursive init is inefficient and can be made iterative by requesting the entire table and looping over it.
    def __init__(self, userID, category=None, parent=None, ctree=None, eaa=None, score=None, dictionary=None, db=user_behavior.DJANGO_DB):
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

        if eaa==None:
            # get from DB (whether Django or dictionary)
            eaa = db.gvix_dict(userID)

        if category:
            self.children = [CategoryTree(userID, x, self, ctree, eaa) for x in ctree.children(category)]
            self.category = category
            self.title = category.title
        else:
            self.children = [CategoryTree(userID, x, self, ctree, eaa) for x in  ctree.children(ctree.concrete_node)]
            self.category = ctree.concrete_node
            self.title = ctree.concrete_node.title

        if dictionary:
            self.dictionary = dictionary
        else:
            self.dictionary = {}

        try:
            self.score = eaa[self.category.id]
        except:
            #if self.category:
            #    self.score = settings.default_eaa[self.category.id]
            #else:
            self.score = ((0, 0, 0, 0))  # * settings.scoringFunction((0,0,0,0)) #This is the root node


    def category_objects(self,category_objects, category):
         return [c for c in category_objects if self.parent == category.id]

    def get_parent(self):
        """
        Return category parent
        """
        return self.parent

    def get_score(self):
        """
        Get the value that the tree is scored on
        """
        return self.score

    def association_coefficient(self):
        """
        Return association_coefficient
        This is a value from 0 to 1- 0 is not associative, 1 is perfectly associative.
        """
        return self.category.association_coefficient

    def get_name(self):
        """
        Return Category title.
        """
        return self.category.title

    def del_dictionary_key(self, key):
        """
        Remove a key from the dictionary.
        """
        del self.dictionary[key]

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

    def get_children(self):
        """
        Return a list of child SimpleTree objects
        """
        return self.children

    def num_nodes(self):
        """
        Return number of children.
        """
        return 1 + sum([c.num_nodes() for c in self.children])

    def __repr__(self):
        """
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
        value = None
        try:
            value = self.dictionary[key]
        except:
            None
        return value

    def print_dictionary_key_values(self):
        """
        Print the Category Tree as a dictionary recursively.
        """
        print self.title
        for key, value in self.dictionary.iteritems():
            print key, ":", value
        for tree in self.children:
            tree.print_dictionary_key_values()

    def subtree_score(self,inkey="score"):
        """
        Returns the sum of inkey scores for a CategoryTree and all its children.
        """
        return self.get_key_value(inkey) + sum([tree.subtree_score(inkey) for tree in self.get_children()])

    #ToDo: Create a more general recursion which is capable of returning values without requiring storage of values in the dictionary. 
    def top_down_recursion(self, function, dict):
        """
        This applies function recursively to the tree in a top-down manner.
        The function is not expected to return a value. Any values generated must be stored in the dictionary.
        """
        function(self, **dict)

        for tree in self.children:
            tree.top_down_recursion(function, dict)

    def bottom_up_recursion(self, function, dict):
        """
        This applies function recursively to the tree in a bottom up manner.
        The function is not expected to return a value. Any values generated must be stored in the dictionary.
        """
        for tree in self.children:
            tree.bottom_up_recursion(function, dict)

        function(self, **dict)

    #TODO:
    # 1: Implement an iterator

    """
    def __iter__(self):
        return self

    def next(self):
        if self.children:
            for child in self.children:
                return child.next()
    """
