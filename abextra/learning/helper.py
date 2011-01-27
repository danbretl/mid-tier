import MySQLdb
import random

try:
    conn = MySQLdb.connect(host = "testsv.abextratech.com",
                           user = "abex_dev",
                           passwd = "abex113",
                           db = "abexmid")
    cursor = conn.cursor()
except MySQLdb.Error, e:
    print "Error %d: %s" % (e.args[0],e.args[1])
    sys.exit(1)


# this could also be converted into an arbitrary depth tree    
def Get_SubTree(cid):
    results = Get_Children(cid)
    const = [Get_SubTree(x) for x in results]    
    if len(const)==0:    
        return (cid,[])
    else:
        return (cid,const)

def Get_Children(cid="NULL"):
    if cid!="NULL":
        query = ("select id from abexmid.events_category where parent_id = %s")
        cursor.execute(query,[cid])
    else:
        query = ("select id from abexmid.events_category where parent_id is NULL")        
        cursor.execute(query)
    return [row[0] for row in cursor.fetchall()]


def generateRandomCategories(numCategories=50):
    query = "select id from events_category order by RAND() limit %s"
    cursor.execute(query,[numCategories])
    return [row[0] for row in cursor.fetchall()]

def insertBehavior(user, category, G, V, I, X):
    query="Insert into behavior_eventactionaggregate (user_id,category_id, g, v, i, x) Values (%s,%s,%s,%s,%s,%s)"
    cursor.execute(query,[user, category, G, V, I ,X])

def genMeanDev():
    mean = int(random.gauss(20,10))
    while mean <= 0: mean = int(random.gauss(20,10))
    d = random.gauss(10,5)
    while d <= 0: d = random.gauss(10,5)
    return (mean,d)

def randomPopulateBehaviorDB(numUsers=100,numCategories=50):
    count=0
    cursor.execute("truncate behavior_eventactionaggregate",list())
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
    query = """select g,v,i,x
             from abexmid.behavior_eventactionaggregate
             where user_id = %s and category_id = %s """
    cursor.execute(query,[uid,cid])
    return cursor.fetchone()
