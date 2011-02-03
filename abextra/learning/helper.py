from events.models import Category
from behavior.models import EventActionAggregate
from django.contrib.auth.models import User
import random


# this could also be converted into an arbitrary depth tree    
def get_subTree(cid=None):
    results = get_children(cid)
    const = [b for a in [get_subTree(x) for x in results] for b in a if a]    
    if len(const)==0: 
        return [cid]
    else:
        if cid:
            return [cid] + const
        else:
            return const

def get_children(category = None):
    return Category.objects.filter(parent__exact=category)


def generateRandomCategories(numCategories=50):
    #query = "select id from events_category order by RAND() limit %s"
    return Category.objects.order_by('?')[:numCategories]

def insertBehavior(userID, categoryID, G, V, I, X):
    #query="Insert into behavior_eventactionaggregate (user_id,category_id, g, v, i, x) Values (%s,%s,%s,%s,%s,%s)"
    user = User.objects.get(id=userID)
    try:
        category = Category.objects.get(id=categoryID)
        EventActionAggregate.objects.create(user=user,category=category, g=G, v=V, i=I,x=X)
    except:
        None

def genMeanDev():
    mean = int(random.gauss(20,10))
    while mean <= 0: mean = int(random.gauss(20,10))
    d = random.gauss(10,5)
    while d <= 0: d = random.gauss(10,5)
    return (mean,d)

def randomPopulateBehaviorDB(numUsers=100,numCategories=50,list_of_users=[]):
    count=0
    if list_of_users:
        numUsers = len(list_of_users)
    while count<numUsers:
        if list_of_users:
            user = list_of_users[count]
            print "user id: ", user
        else:
            user = count
        for category in [x+1 for x in range(numCategories)]:
            mean,d=genMeanDev()
            G=random.gauss(mean,d)
            while G <= 0: G = random.gauss(mean,d)
            mean,d=genMeanDev()
            V=random.gauss(mean,d)
            while V <= 0: V = random.gauss(mean,d)
            mean,d=genMeanDev()
            I=random.gauss(mean,d)
            while I <= 0: I = random.gauss(mean,d)
            mean,d=genMeanDev()
            X=random.gauss(mean,d)
            while X <= 0: X = random.gauss(mean,d)
            print "Inserting : User=",user, " Category=", category," GVIX=",G,",",V,",",I,",",X
            insertBehavior(user,category,G,V,I,X)
        count=count+1


def get_node_val(uid,cid):
    try: 
        e = EventActionAggregate.objects.values_list('g','v','i','x').get(user=uid,category=cid)
    except:
        return None
    return  e
