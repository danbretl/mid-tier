from django.contrib.auth.models import User
from behavior.models import EventActionAggregate
import math

#from django.contrib.auth.models import User

Gm = 5                # G Multiplier in the scoring function
Vm = 1                 # V Multiplier in the scoring function
Im = 1                 # I Multiplier in the scoring function
Xp = 0.4               # X's power in scoring function
learning_constant = 500 # learning constant. Affects learning speed.
                       # Higher values result in slower learning

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
    return (lambda y: ((F(y[0]**g)*G + (y[1]**v)*V + (y[2]**i)*I + learning_constant) *(X**y[3]))) 

scoringFunction = scoring_function((Gm,Vm,Im,Xp),(0.4,1,1))

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
max_probability = 0.20

