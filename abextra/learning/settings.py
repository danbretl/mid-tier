from django.contrib.auth.models import User

#from django.contrib.auth.models import User

Gm = 50                 # G Multiplier in the scoring function
Vm = 1                 # V Multiplier in the scoring function
Im = 1                 # I Multiplier in the scoring function
Xp = 0.7               # X's power in scoring function
learning_constant = 500  # learning constant. Affects learning speed.
                       # Higher values result in slower learning

N = 40                 # Number of recommendations to the end user

def scoring_function(tup = (1,1,1,0.9), pow = (3,2,1)):
    G,V,I,X = tup
    g,v,i = pow
    return (lambda y: ((y[0]**g)*G + (y[1]**v)*V + (y[2]**i)*I + learning_constant )*(X**y[3]) ) 

scoringFunction = scoring_function((Gm,Vm,Im,Xp),(1,1,1))

abstract_scoring_function = scoring_function((Gm,Vm,Im,Xp),(1,1,1))

def get_default_user():
    return User.objects.get(username="default_behavior")

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

