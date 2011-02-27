"""
This file is for simulation of user behavior and preferences for the purpose of working
with the testing_framework module. It makes simple assumptions about user behavior and then
sees if the algorithm can learn reasonably well towards those preferences. This is in
contrast to many of the tests in testing_framework, which offer simple, discrete preferences
that are easier to learn to.
This functionality is intended for use currently only within the Django Testing framework.
Author: Vikas Menon
Date Created: 2/26/2011
"""

from collections import defaultdict

import ml
from events.utils import CachedCategoryTree

# behavior enum
[GO, VIEW, IGNORE, XOUT] = range(4)

class SimulatedPreference:
    """
    this represents a single kind of preference for a single category, to be
    used in a simulation, such as love, hate, or indifferent
    """
    def __init__(self, name, g_prob, v_prob, i_prob, x_prob):
        """given probabilities of Going, Viewing, Ignoring or Xing a category"""
        self.name = name
        
        total = g_prob + v_prob + i_prob + x_prob
        if (total != 1):
            raise ValueError("G+V+I+X must add up to 1, not " + str(total))
        self.distribution = zip([GO, VIEW, IGNORE, XOUT],
                                [g_prob, v_prob, i_prob, x_prob])
    
    def sample_action(self):
        """get one random from this preference distribution"""
        return ml.sample_distribution(self.distribution)[0]
    
    def __repr__(self):
        return "<Preference: " + self.name + ">"

class PreferenceTransitionMatrix:
    """
    This is used to assign preferences to a tree. It contains both the
    distribution of preferences at the top level and a transition matrix
    showing how one parent's preference affects its children
    """
    def __init__(self):
        """initialize the matrix and distribution, right now with defaults"""
        self.love = SimulatedPreference("Love", .5, .3, .2, 0)
        self.indifferent = SimulatedPreference("Indifferent", .1, .2, .5, .2)
        self.hate = SimulatedPreference("Hate", 0, .1, .2, .7)
        
        self.original_distribution = [(self.love, .3), 
                                      (self.indifferent, .4), 
                                      (self.hate, .3)]
        
        # thought- there is a way to write this much more succinctly. For
        # example, could be imported as a tab delimited matrix. Not yet
        # important at all, but if we make our simulation more complicated,
        # something to think about it.
        
        self.transition_matrix = {}
        self.transition_matrix[self.love] = [(self.love, .8), 
                                             (self.indifferent, .2), 
                                             (self.hate, 0)]
        self.transition_matrix[self.indifferent] = [(self.love, .3), 
                                                    (self.indifferent, .4), 
                                                    (self.hate, .3)]
        self.transition_matrix[self.hate] = [(self.love, 0), 
                                             (self.indifferent, .2), 
                                             (self.hate, .8)]
    
    def get_preference_dictionary(self, ct):
        """passed a CachedCategoryTree, return category->preference dict"""
        # pass around a dictionary to add
        ret = {}
        
        # start at the concrete node's children
        top_level = ct.children(ct.concrete_node)
        
        for n in top_level:
            # assign randomly
            ret[n] = ml.sample_distribution(self.original_distribution)[0]
            self.__recurse_ct(ct, n, ret)
        
        return ret
            
    def __recurse_ct(self, ct, n, d):
        """given a cached category tree, a current node, and a dictionary of
        category->preference mappings"""
        current_pref = d[n]
        print current_pref
        for child in ct.children(n):
            d[child] = ml.sample_distribution(self.transition_matrix[current_pref])[0]
            self.__recurse_ct(ct, child, d)


class Person():
    def __init__(self, user=None):
        self.last_actions = None
        self.last_recommendation = None
        if user:
            self.user = user
            self.delete_user = False
        else:
            # Create and assign a new user.
            # if necessary later delete the user as well. But this might not be 
            # necessary since in Django we will be working with a fresh database 
            # that will in any case be destructed at the end of testing.
            self.delete_user = True
            success = False
            count = 0
            while not success:
                count += 1
                try:
                    self.user = User(username="test"+str(count), 
                                     password='test'+str(count))
                    self.user.save()
                    success = True
                except:
                    success = False
                    
        for c in Category.objects.all():
            try:
                #See if event action aggregate exists.If it does, reset it to default.
                eaa = EventActionAggregate.objects.get(user=self.user,category=c)
            except:
                #Else create one.
                eaa = EventActionAggregate(user=self.user, category=c)
            
            eaa.g, eaa.v, eaa.i, eaa.x = 0, 0, 0, 0
            eaa.save()
        

    def __del__(self):
        if self.delete_user:
            self.user.delete()
        self.reset_user_behavior()


    def push_recommendations(self):
        categories = [c.id for c in
                      ml.sample_distribution(ml.recommend_categories(self.user),settings.N)]
        self.last_recommendations = categories[:]
        self.last_actions = map(self.get_action,
                                self.last_recommendations)
        
        self.update_user_category_behavior(
            (self.last_actions.count(a)
             for a in [GO, VIEW, IGNORE, XOUT]))
        return(self.last_actions)

    def update_user_category_behavior(self,category_id,(g,v,i,x)=(0,0,0,0)):
        """change the user's aggregate action by given (g,v,i,x) tuple"""
        eaa = EventActionAggregate.objects.get(user=self.user, 
                                               category__id=category_id)
        eaa.g += g
        eaa.v += v
        eaa.i += i
        eaa.x += x
        eaa.save()
    
    
class DeterministicPerson(Person):
    """
    A Person that likes a specific subset of categories and always goes to them,
    and dislikes (always X's) everything else. This allows it to have
    precision and recall
    """
    def __init__(self, liked_category_ids):
        """
        initialized with a list of category ID's the user likes (he will
        dislike all others)
        """
        Person.__init__(self)
        self.liked_category_ids = liked_category_ids
    
    def get_action(self, category_id, event_id=None):
        """return G if the user likes it and X if he doesn't"""
        if category_id in self.liked_category_ids:
            return GO
        else:
            return XOUT
    
    def get_precision_recall(self):
        """get the last precision and recall"""
        precision = (float(self.last_actions.count(GO)) /
                     len(self.last_actions))

        recall = (len(set(self.liked_category_ids).intersection(
            set(self.last_recommendations))) / len(self.liked_category_ids))


class DiscretePreferencePerson(Person):
    """
    A user whose interests fall into discrete Preference objects, one for each
    user
    """
    def __init__(self, preference_map):
        """given a dictionary of categories to Preference objects"""
        self.preference_map = preference_map

    def get_action(self, category):
        """given a category, return an action (G, V, I, or X)"""
        return self.preference_map[category].sample_action()

class TransitionSimulatedPerson(DiscretePreferencePerson):
    """
    represents a simulated user and his preferences for the full set of
    categories. This one has preferences for each that are generated
    from a transition matrix
    """
    def __init__(self):
        """initialize this user's behavior as a category->preference mapping"""
        transition_matrix = PreferenceTransitionMatrix()
        ct = CachedCategoryTree()
        pref_map = transition_matrix.get_preference_dictionary(ct)
        DiscretePreferencePerson.__init__(self, pref_map)
