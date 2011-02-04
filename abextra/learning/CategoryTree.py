from events.models import Category
from behavior.models import EventActionAggregate
from django.contrib.auth.models import User
import settings

class CategoryTree:
    def __init__(self, userID, category=None, score=None,dict=None):
        """A Tree for a user is represented recursively as a collection of trees, 
        Each tree is for a specific user.
        The name of a tree node is the category name otherwise defaults to ROOT
        the value is calculated from the persisted representation of the tree
        much the user likes this, and optionally children"""
        self.children = [CategoryTree(userID,x) for x in  Category.objects.filter(parent__exact=category)]
        self.category = category
        if category:
            self.title = category.title
        else:
            self.title = "ROOT"
        ## adding this as a feature so we can store any number of key-value pairs inside the dictionary
        if dict: 
            self.dictionary = dict
        else:
            self.dictionary = {}
        try:
            self.score = EventActionAggregate.objects.values_list('g','v','i','x').get(user=userID,category=self.category)
        except:
            default_user = settings.default_user
            if self.category:
                self.score = EventActionAggregate.objects.values_list('g','v','i','x').get(user=default_user,category=self.category)
            else:
                self.score = ((0,0,0,0))# * settings.scoringFunction((0,0,0,0)) #This is the root node

    def get_score(self):
        """get the value that the tree is scored on"""
        return self.score

    def get_key_value(self, key):
        value = None
        try:
            value = self.dictionary[key]
        except:
            None
        return value
    
    def association_constant(self):
        """value from 0 to 1- 0 is not associative, 1 is perfectly
        associative"""
        return self.category.association_coefficient

    def return_flat_tree(self,key): 
        return self.category

    def get_name(self):
        return self.category.title

    def get_category_scores_dictionary(self,keys):
        if self.category:
            list = [(self.category.id,[self.dictionary[key] for key in keys])]
        else:
            list =[]
        list += [b for a in [tree.get_category_scores_dictionary(keys) for tree in self.children] for b in a]
        return list
    
    def get_children(self):
        """return a list of child SimpleTree objects"""
        return self.children
    
    def num_nodes(self):
        return 1 + sum([c.num_leaves() for c in self.children])
    
    def __repr__(self):
        """string representation in nested parentheses"""
        ret = "'" + self.title + "'" + "=" + str(self.score)

        if len(self.children) > 0:
            ret += "(" + ",".join(map(str, self.children)) + ")"
        return ret

    def insert_key_value(self,key,value):
        self.dictionary[key]=value

    def print_dictionary_key_values(self):
        print self.title
        for key,value in self.dictionary.iteritems():
            print key, ":", value
        for tree in self.children:
            tree.print_dictionary_key_values()

    #TODO:
    # 1: Implement an iterator
    # 2: Implement a map function to perform top down recursion
    # 3: Implement a map function to perform bottom up recursion

            
    """def __iter__(self):
        return self
    
    def next(self):
        if self.children:
            for child in self.children:
                return child.next()"""

    
