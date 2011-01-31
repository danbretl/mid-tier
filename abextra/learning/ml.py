#
# Author: Vikas Menon
# Date: 1/25/2011
# First attempt at a recommendation engine
#

import numpy
import random
import helper

def recommend_categories(user):
    return tree_walk_algorithm(user)

def recommend_categories_only_subchildren(user, category):
    return tree_walk_algorithm(user, category)

def tree_walk_algorithm(user, category=None, N = 20):
    """
    All algorithms follow this same fundamental structure
        Input: UserID as input 
        N is the number of events to return and has a default of 20
    Output: Ordered list of EventIDs
    """
    rootNodes = helper.get_children(category)
    Category_Scores = get_category_score(user,category)
    #print "Category_Scores: ", Category_Scores
    TotalScore = sum ([x[1] for x in Category_Scores]) + .0001
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
def scoring_function(tup = (1,1,1,0.9), pow = (1,1,1)):
    G,V,I,X = tup
    g,v,i = pow
    return (lambda y: ((y[0]**g)*G + (y[1]**v)*V + (y[2]**i)*I)/(X**y[3])  )

scoringFunction = scoring_function((1,1,1,0.9))

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


def child_scores_combinator(scores):
    scores = [score for score in scores if score]          # filter out none type scores
    return (sum([x[0] for x in scores]),sum([x[1] for x in scores]),sum([x[2] for x in scores]), sum([x[3] for x in scores]))

def get_category_score(uid,cid):
    child_scores = [get_category_score(uid, x) for x in helper.get_children(cid)]
    child_scores = [b for a in child_scores for b in a]
    score = helper.get_node_val(uid,cid)
    parent_score = (cid,scoringFunction(score)) if score else (cid,scoringFunction((0,0,0,0)))
    if cid:
        return parent_child_score_combinator(parent_score,child_scores) if child_scores else [parent_score]
    else:
        return child_scores

def parent_child_score_combinator(parent_category_score,category_scores):
    number_of_siblings = len(category_scores)
    simple_constant = 0.5 / number_of_siblings
    # print "Parent Category Score: ", parent_category_score
    # print "Child category scores: ", category_scores
    score = sum([x[1] for x in category_scores])
    return [(parent_category_score[0],parent_category_score[1] + score)] + category_scores

