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

import sys
import time
from collections import defaultdict

import numpy as np
from matplotlib import pyplot as plt
from django.contrib.auth.models import User

import ml
import settings
from simulation_shared import *
import user_behavior
from events.utils import CachedCategoryTree
from events.models import Category


### FUNCTIONS ###

def get_category_id(string):
    """given the title of a category, return its id"""
    c = Category.objects.get(title=string)
    return c.id


def get_category_string(id):
    c = Category.objects.get(id=id)
    return c.title


def finish_plot(outfile):
    """
    given an output file, write and clear the figure- if None
    is given, don't save
    """
    if outfile:
        plt.savefig(outfile)
        plt.cla()


def freq_dict(iter):
    """given an iterable, return a dictionary mapping each item to
    the number of times it appears"""
    freq = defaultdict(int)
    for e in iter:
        freq[e] += 1
    return freq


def print_carriage_return(s):
    """print a string and then return to the beginning of the line"""
    print s, "\r",
    sys.stdout.flush()

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
        
        self.original_distribution = [(self.love, 0), 
                                      (self.indifferent, .6), 
                                      (self.hate, .4)]
        
        # thought- there is a way to write this much more succinctly. For
        # example, could be imported as a tab delimited matrix. Not yet
        # important at all, but if we make our simulation more complicated,
        # something to think about it.
        
        self.transition_matrix = {}
        self.transition_matrix[self.love] = [(self.love, .8), 
                                             (self.indifferent, .2), 
                                             (self.hate, 0)]
        self.transition_matrix[self.indifferent] = [(self.love, .2), 
                                                    (self.indifferent, .5), 
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
            ret[n.id] = ml.sample_distribution(self.original_distribution)[0]
            self.__recurse_ct(ct, n, ret)
        
        return ret
            
    def __recurse_ct(self, ct, n, d):
        """given a cached category tree, a current node, and a dictionary of
        category->preference mappings"""
        current_pref = d[n.id]
        for child in ct.children(n):
            d[child.id] = ml.sample_distribution(self.transition_matrix[current_pref])[0]
            self.__recurse_ct(ct, child, d)


class Round:
    """represents the results of a round of recommendations"""
    def __init__(self, recommendations, actions):
        """given a matching list of recommendations and of actions"""
        self.recommendations = recommendations
        self.actions = actions
        self.N = len(recommendations)
        
        # save G, V, I, and X
        (self.G, self.V, self.I, self.X) = self.gvix()
    
    def gvix(self):
        """return the tuple of G, V, I, and X quantities in this round"""
        return [self.actions.count(a) for a in ACTIONS]


class Person:
    """
    this is the class inherited by all Persons- it cannot be used itself
    """
    def __init__(self, user=None, db=user_behavior.DJANGO_DB):
        """optionally given a user, otherwise creates one. Optionally given
        a DB, otherwise uses default Django DB"""
        # rounds are a 2D array- first dimension is the round number, second
        # is the different trials for that round (so they can be averaged
        # easily)
        self.rounds = []
        self.db = db
        
        # keep a cached category tree
        self.ctree = CachedCategoryTree()
        
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
        
        # initialize user
        self.db.initialize_user(self.user, self.delete_user)
    
    def run_rounds(self, num_rounds=1, num_trials=1,
                         num_recommendations=settings.N):
        """the number of rounds is the list of individual recommendation
        batches, the trials is the number of times the experiment is 
        repeated (after resetting), and the number of recommendations is the
        number each"""
        trials = []
        for t in range(num_trials):
            print_carriage_return("Trial " + str(t))
            
            rounds = []
            for i in range(num_rounds):
                print_carriage_return("Round " + str(i))
                r = self.run_round(num_recommendations)
                rounds.append(r)
            trials.append(rounds)
            self.db.clear()
        
        # divide it so that it is a list of the different trials for each
        self.rounds = zip(*trials)
    
    def run_round(self, num_recommendations=settings.N):
        """
        run a single round with the given number of recommendations, adding 
        to the behavior database and returning the Round object
        """
        cats = ml.recommend_categories(self.user, ctree=self.ctree,
                                        db=self.db).items()
        categories = [c.id for c in
                      ml.sample_distribution(cats, settings.N)]
        actions = map(self.get_action, categories)
        
        r = Round(categories, actions)
        
        # add behavior and to rounds
        self.db.update_from_round(self.user, r)
        return r
    
    def apply_average_rounds(self, func):
        """
        given a function, return it averaged over different trials of each
        round. If the function returns a list or tuple, return a tuple of
        those averages"""
        averages = []
        for r in self.rounds:
            # apply to different trials
            vals = map(func, r)
            # use one example of a type to figure out what to do
            cl = vals[0].__class__
            if cl == tuple or cl == list:
                # unzip (to divide into each tuple) and then find the mean
                # of each
                averages.append(map(np.mean, zip(*vals)))
            elif cl == int or cl == float:
                averages.append(np.mean(vals))
            else:
                raise TypeError("function returns " + str(cl) + ", not int, " +
                                "float, list or tuple")
        
        # if necessary, unzip averages before returning
        if cl == tuple or cl == list:
            return zip(*averages)
        else:
            return averages
    
    def plot_gvix(self, outfile=None):
        """plot the G, V, I and X over rounds"""
        # get the sequences of G, V, I, and X separately
        action_sequences = self.apply_average_rounds(lambda r: r.gvix())
        for n, a in zip(ACTION_NAMES, action_sequences):
            plt.plot(a, label=n)
        plt.legend()
        finish_plot(outfile)
    
    def __del__(self):
        """clear info"""
        self.db.clear()


class DeterministicPerson(Person):
    """
    A Person that likes a specific subset of categories and always goes to them,
    and dislikes (always X's) everything else. This allows it to have
    precision and recall
    """
    def __init__(self, liked_category_ids, user=None, db=user_behavior.DJANGO_DB):
        """
        initialized with a list of category ID's the user likes (he will
        dislike all others)
        """
        Person.__init__(self, user, db)
        self.liked_category_ids = set(liked_category_ids)
    
    def get_action(self, category_id, event_id=None):
        """return G if the user likes it and X if he doesn't"""
        if category_id in self.liked_category_ids:
            return GO
        else:
            return XOUT
    
    def get_precision_recall(self, r):
        """get precision and recall of given round"""
        precision = float(r.G) / r.N
        recall = (float(len(self.liked_category_ids.intersection(
                    set(r.recommendations)))) / len(self.liked_category_ids))
        
        return (precision, recall)

    def plot_precision_recall(self, outfile):
        """plot precision recall over history"""
        precision, recall = zip(*map(self.get_precision_recall, self.rounds))
        plt.plot(precision, label="Precision")
        plt.plot(recall, label="Recall")
        plt.legend()
        finish_plot(outfile)


class DiscretePreferencePerson(Person):
    """
    A user whose interests fall into discrete Preference objects, one for each
    user
    """
    def __init__(self, preference_map, user=None, db=None):
        """given a dictionary of categories to Preference objects"""
        Person.__init__(self, user, db)
        self.preference_map = preference_map
        
        print freq_dict(self.preference_map.values())

    def get_action(self, category):
        """given a category, return an action (G, V, I, or X)"""
        return self.preference_map[category].sample_action()
    
    def get_preference_distribution(self, r, preferences):
        """given a round and an ordered list of preferences, return the
        number in each preference"""
        #return dict([(p.name, preferences.count(p)) 
        #                for p in set(preferences)])
        pref_each = [self.preference_map[c] for c in r.recommendations]
        return [pref_each.count(p) for p in preferences]
    
    def plot_preference_distribution(self, outfile=None):
        """create a plot of how many recommendations are given in each round to
        each preference"""
        prefs = list(set(self.preference_map.values()))
        func = lambda r: self.get_preference_distribution(r, prefs)
        average_preferences = self.apply_average_rounds(func)
        
        print prefs
        print average_preferences
        for pref, seq in zip(prefs, average_preferences):
            plt.plot(seq, label=pref.name)
        plt.legend()
        
        finish_plot(outfile)

class TransitionSimulatedPerson(DiscretePreferencePerson):
    """
    represents a simulated user and his preferences for the full set of
    categories. This one has preferences for each that are generated
    from a transition matrix
    """
    def __init__(self, user=None, db=None):
        """initialize this user's behavior as a category->preference mapping"""
        transition_matrix = PreferenceTransitionMatrix()
        ct = CachedCategoryTree()
        pref_map = transition_matrix.get_preference_dictionary(ct)
        DiscretePreferencePerson.__init__(self, pref_map, user, db=db)

