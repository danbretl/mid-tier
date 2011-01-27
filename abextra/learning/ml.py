#
# Author: Vikas Menon
# Date: 1/25/2011
# First attempt at a recommendation engine
#

import numpy
import random
import helper

# All algorithms follow this same fundamental structure
# Input: UserID as input 
#        N is the number of events to return and has a default of 20
# Output: Ordered list of EventIDs


def TrivialAlgorithm(UserID, CategoryID="NULL", N = 20):
    rootNodes = helper.Get_Children(CategoryID)
    Category_Scores = [(category,User_Category_Score(UserID,category))for category in rootNodes if User_Category_Score(UserID,category)]
    #print "Category_Scores: ", Category_Scores
    TotalScore = sum ([x[1] for x in Category_Scores])
    Normalized_Scores = [(x[0],x[1]*1.0/TotalScore) for x in Category_Scores]
    #Flattened_Distribution = flatten(Normalized_Scores)
    Flattened_Distribution = Normalized_Scores
    return SampleDistribution(Flattened_Distribution, N)
    

def SummaryScore(Sample_Distribution):
    dict = {}
    for x in Sample_Distribution:
        try:
            dict[x]+=1
        except:
            dict[x]=1
    return dict


#def trivial_Algorithm(UserID, N = 20):
#    distribution = get_distribution(uid)        #distribution is a list of (CategoryID,score) where score is between 0 and 1
                                                #The sum of all scores in the tuple adds up to 1
# usage example:
# f = ScoringFunction((2,2,2,3),(2,2,2,1))
# print f((2,2,2,1))
def ScoringFunction(tup = (1,1,1,1), pow = (1,1,1,1)):
    G,V,I,X = tup
    g,v,i,x = pow
    return (lambda y: ((y[0]**g)*G + (y[1]**v)*V + (y[2]**i)*I)/(X*(y[3]**x))  )

def User_Category_Score(uid,cid):
    scoreFunction = ScoringFunction((3,2,1,1))
    score = helper.Get_Node_Val(uid,cid)
    if score: 
        return scoreFunction(score)
    return None


def SampleDistribution(distribution,trials):
    # convert into a cumulative distribution
    # Generate random number and return numbers per range
    CDFDistribution = numpy.cumsum([x[1] for x in distribution])
    #print "Distribution: ",  CDFDistribution
    returnList = []
    for i in range(trials):
        value = random.random()
        #todo: use binary search to scan the array and locate count faster
        count = 0
        for count in range(len(distribution)):
            if (value < CDFDistribution[count]): break
        returnList += [(distribution[count])[0]]
    return returnList
        
