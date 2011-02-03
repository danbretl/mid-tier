from django.contrib.auth.models import User

Gm = 1                 # G Multiplier in the scoring function
Vm = 1                 # V Multiplier in the scoring function
Im = 1                 # I Multiplier in the scoring function
Xp = 0.9               # X's power in scoring function
learning_constant = 3  # learning constant. Affects learning speed.
                       # Higher values result in slower learning

def scoring_function(tup = (1,1,1,0.9), pow = (1,1,1)):
    G,V,I,X = tup
    g,v,i = pow
    return (lambda y: ((y[0]**g)*G + (y[1]**v)*V + (y[2]**i)*I)/(X**y[3]) + learning_constant ) 

scoringFunction = scoring_function((Gm,Vm,Im,Xp))

default_user = User.objects.get(username="default_behavior")
