from django.contrib.auth.models import User
from behavior.models import EventActionAggregate
import math

#from django.contrib.auth.models import User


Gm = 15                # G Multiplier in the scoring function
Vm = 4                 # V Multiplier in the scoring function
Im = 1                 # I Multiplier in the scoring function
Xp = 0.4               # X's power in scoring function
learning_constant = 50 # learning constant. Affects learning speed.
                       # Higher values result in slower learning
#resistance is a measure of how stubborn a category is in getting selected.
#This number should always be less than the learning_constant otherwise
#the algorithm won't be able to distinguish between an X'ed category
#from a category that has never been visited by a user.
resistance = 0

N = 20                 # Number of recommendations to the end user

#slows down the GVIX scoring function.
def F(x):
    num = 1
    if x < num:
        return x
    else:
        return num + math.log(x-num + 1)

def scoring_function(tup = (1,1,1,0.9), pow = (3,2,1)):
    G,V,I,X = tup
    g,v,i = pow
    #return (lambda y: ((F(y[0])**g)*G + (y[1]**v)*V + (y[2]**i)*I)*(X**y[3]) + learning_constant)
    return (lambda y: (((y[0]**g)*G + (y[1]**v)*V + (y[2]**i)*I + learning_constant) *(X**y[3])) + resistance) 

scoringFunction = scoring_function((Gm,Vm,Im,Xp),(1.5,1,1))

abstract_scoring_function = scoring_function((Gm,Vm,Im,Xp),(2,1,1))

def get_default_user():
    return User.objects.get(username="default_behavior")

default_eaa = dict((ea.category_id,(ea.g,ea.v,ea.i,ea.x)) for ea in EventActionAggregate.objects.filter(user=get_default_user()))

def mean(lst):
    if lst:
        return (1.0 * sum(lst))/len(lst)
    else:
        return 0.0

def topN_function(N):
    if N>0:
        return lambda lst: mean(sorted(lst)[-N:])
    else:
        return lambda lst: 0.0


def mod_topN_function(N):
    if N > 1:
        return lambda lst:lst[0]*mean(sorted(lst[1:])[-N:])/(sum(lst[1:]) + 1)
    else:
        return lambda lst: sum(lst)

top3Score = topN_function(3)

#top3Score = mod_topN_function(3)

#This caps the probability of any CategoryTree node getting selected in a probabilistic walk.
max_probability = 0.25

