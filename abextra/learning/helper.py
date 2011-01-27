from events.models import Category
from behavior.models import EventActionAggregate
import random


# this could also be converted into an arbitrary depth tree    
def Get_SubTree(cid=None):
    results = get_children(cid)
    const = [Get_SubTree(x) for x in results]    
    if len(const)==0:    
        return (cid,[])
    else:
        return (cid,const)

def get_children(category = None):
    return Category.objects.filter(parent__exact=category)


def generateRandomCategories(numCategories=50):
    #query = "select id from events_category order by RAND() limit %s"
    return Category.objects.order_by('?')[:numCategories]

def insertBehavior(userID, category, G, V, I, X):
    #query="Insert into behavior_eventactionaggregate (user_id,category_id, g, v, i, x) Values (%s,%s,%s,%s,%s,%s)"
    EventActionAggregate.objects.create(user_id=userID,category_id=category, g=G, v=V, i=I,x=X)


def genMeanDev():
    mean = int(random.gauss(20,10))
    while mean <= 0: mean = int(random.gauss(20,10))
    d = random.gauss(10,5)
    while d <= 0: d = random.gauss(10,5)
    return (mean,d)

def randomPopulateBehaviorDB(numUsers=100,numCategories=50):
    count=0

    while count<numUsers:
        categories = generateRandomCategories(numCategories)
        for category in categories:
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
            insertBehavior(count,category,G,V,I,X)
        count=count+1

    
def CategoryDistribution(uid):
    categories=Get_Children()
    print [(y,Get_SubTree_Score(uid,y)) for y in Get_Children()]

# Combine scores for children
# Combine scores for node + children
def Get_SubTree_Score(uid,cid):
    children = Get_Children(cid)
    if len(children) == 0 : return Get_Node_Val(uid,cid)
    else: return Parent_Child_Score_Combinator(Get_Node_Val(uid,cid), [Get_SubTree_Score(uid,x) for x in Get_Children(cid)])

def Parent_Child_Score_Combinator(score,scores):
    return Child_Scores_Combinator(scores + [score])

def Child_Scores_Combinator(scores):
    scores = [score for score in scores if score]          # filter out none type scores
    return (sum([x[0] for x in scores]),sum([x[1] for x in scores]),sum([x[2] for x in scores]), sum([x[3] for x in scores]))

def Get_Node_Val(uid,cid):
    try: 
        e = EventActionAggregate.objects.values_list('g','v','i','x').get(user=uid,category=cid)
    except:
        return None
    return  e
