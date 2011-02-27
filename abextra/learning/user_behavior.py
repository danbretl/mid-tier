"""
These classes abstract away away the user behavior database. They are
relevant because in the testing framework, we don't want to deal with
a database (since we don't require persistence)- we can just keep 
them in a dictionary. This makes it easy to switch between 
the database and the dictionary
"""

import collections

from simulation_shared import *
from behavior.models import EventActionAggregate
from django.contrib.auth.models import User
from events.models import Category


class UserBehaviorDB:
    """represents either a dictionary or Django DB"""
    def update_from_round(self, u, round):
        """given a round of event actions"""
        for c, a in zip(round.recommendations, round.actions):
            self.perform_action(u, c, a)

    def initialize_user(self, u, delete_user=False):
        """not all need this"""
        pass
    
    def clear(self):
        """not all need this"""
        pass


class UserBehaviorDict(UserBehaviorDB):
    """
    Stores user behavior in a dictionary- use in a testing environment
    where we don't need it to be persistent
    """
    def __init__(self):
        """create user dictionary"""
        # store as dict mapping users to dicts of category-> [G,V,I,X] list
        # didn't use tuple since that prevents item assignment
        factory = lambda: collections.defaultdict(lambda: [0,0,0,0])
        self.user_dict = collections.defaultdict(factory)
    
    def perform_action(self, u, c, action):
        """alter the G, V, I, X of the given user"""
        self.user_dict[u][c][ACTIONS.index(action)] += 1

    def gvix_dict(self, u):
        """return a category->(G, V, I, X) mapping"""
        return self.user_dict[u]


class UserBehaviorDjangoDB(UserBehaviorDB):
    """
    Abstracts away the interface with the Django DB in order to be easily
    switchable
    """
    def __init__(self):
        """just keep a list of users"""
        self.users = []
    
    def initialize_user(self, u, delete_user=True):
        """add user to the EventActionAggregate"""
        self.users.append((u, delete_user))
        
        for c in Category.objects.all():
            try:
                #See if event action aggregate exists.If it does, reset it to default.
                eaa = EventActionAggregate.objects.get(user=u,category=c)
            except:
                #Else create one.
                eaa = EventActionAggregate(user=u, category=c)
            
            eaa.g, eaa.v, eaa.i, eaa.x = 0, 0, 0, 0
            eaa.save()
    
    def perform_action(self, u, c, action):
        """given a category and its action, change the user's aggregate"""
        eaa = EventActionAggregate.objects.get(user=u, 
                                               category__id=c)
        
        if action == GO:
            eaa.g += 1
        elif action == VIEW:
            eaa.g += 1
        elif action == IGNORE:
            eaa.i += 1
        elif action == XOUT:
            eaa.x += 1
        
        eaa.save()
    
    def gvix_dict(self, u):
        """return a dictionary mapping category id to (G, V, I, X)"""
        eaa = EventActionAggregate.objects.filter(user=u)
        return dict((ea.category_id,(ea.g,ea.v,ea.i,ea.x)) for ea in eaa)

    def clear(self):
        """clear records from the DB"""
        for u, d in self.users:
            if d:
                u.delete()
            self.reset_user_behavior(u)
    
    def reset_user_behavior(self, u):
        """clear a user's behavior"""
        for category in Category.objects.all():
            eaa = EventActionAggregate.objects.get(user=u, category=category)
            eaa.g, eaa.v, eaa.i, eaa.x = 0, 0, 0, 0
            eaa.save()
            #except:
                # TODO: what exception is this meant to cover?
            #    pass

# Normally I wouldn't create a global variable like this, but it's used in a
# lot of function defaults
DJANGO_DB = UserBehaviorDjangoDB()