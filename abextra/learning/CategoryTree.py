from events.models import Category
from behavior.models import EventActionAggregate
from django.contrib.auth.models import User
import settings

class CategoryTree:
    def __init__(self, userID, category=None, score=None):
        """A Tree for a user is represented recursively as a collection of trees, 
        Each tree is for a specific user.
        The name of a tree node is the category name otherwise defaults to ROOT
        the value is calculated from the persisted representation of the tree
        much the user likes this, and optionally children"""
        self.children = [filteredList for filteredList in [CategoryTree(userID,x) for x in  Category.objects.filter(parent__exact=category)] if filteredList]
        self.category = category
        try:
            self.score = EventActionAggregate.objects.values_list('g','v','i','x').get(user=userID,category=self.category)
        except:
            default_user = settings.default_user
            if self.category:
                self.score = EventActionAggregate.objects.values_list('g','v','i','x').get(user=default_user,category=self.category)
            else:
                #This is the root node and its score does not matter.
                self.score = (0,0,0,0)
    
    def get_score(self):
        """get the value that the tree is scored on"""
        return self.score
    
    def association_constant(self):
        """value from 0 to 1- 0 is not associative, 1 is perfectly
        associative"""
        return self.category.association_coefficient
    
    def get_children(self):
        """return a list of child SimpleTree objects"""
        return self.children
    
    def num_nodes(self):
        return 1 + sum([c.num_leaves() for c in self.children])
    
    def __repr__(self):
        """string representation in nested parentheses"""
        if self.category:
            ret = "'" + self.category.title + "'" + "=" + str(self.score)
            if self.category.association_coefficient != 0:
                ret += "[" + str(self.category.association_coefficient) + "]"
        else:
            ret = "ROOT = "
        if len(self.children) > 0:
            ret += "(" + ",".join(map(str, self.children)) + ")"
        return ret
