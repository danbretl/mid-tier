#
# Author: Vikas Menon
# Date: 1/25/2011
# First attempt at a recommendation engine
#

import numpy
import random
import helper
import settings
from events.models import Category
import CategoryTree

def recommend_categories(user):
    return tree_walk_algorithm(user)

def recommend_categories_only_subchildren(user, category):
    return tree_walk_algorithm(user, category)

def score_algorithm(user, category=None, N = 20):
    """
    All algorithms follow this same fundamental structure
        Input: User as input 
        N is the number of events to return and has a default of 20
    Output: Ordered list of EventIDs
    """
    Category_Scores = get_category_score(user,category)
    TotalScore = sum ([x[1] for x in Category_Scores])
    if TotalScore!=0:
        Normalized_Scores = [(x[0],x[1]*1.0/TotalScore) for x in Category_Scores]
    else:
        size = len(Category_Scores) 
        Normalized_Scores = [(x[0],1.0/size) for x in Category_Scores]
    #Flattened_Distribution = flatten(Normalized_Scores)
    #print "Normalized Scores: ", Normalized_Scores
    return SampleDistribution(Normalized_Scores, N)


def tree_walk_algorithm(user,category=None, N=20):
    tree = CategoryTree(user)


def SummaryScore(Sample_Distribution):
    dict = {}
    for x in Sample_Distribution:
        try:
            dict[x]+=1
        except:
            dict[x]=1
    return dict

def normalize(lst):
    """normalize all values so they add up to 1"""
    s = float(sum(lst))
    if s!=0:
        return [e / s for e in lst]
    else:
        return [1/len(lst) for e in lst]

def decrease(x, d):
    """decrease d by a factor that is smaller
    and smaller the greater the difference is"""
    # limit
    if x == 0:
        return d
    return d * (1 - math.exp(-d/x))

def flatten_expo(x, lst):
    """remove part of the distance towards the mean"""
    m = sum(lst) / float(len(lst)) # mean
    
    newlst = []
    for e in lst:
        if e > m:
            newlst.append(m+decrease(x, e-m))
        else:
            newlst.append(m-decrease(x, m-e))
    return normalize(newlst)


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

def get_category_scores(uid,cid):
    child_scores = [get_category_scores(uid, x) for x in helper.get_children(cid)]
    child_scores = [b for a in child_scores for b in a]
    score = helper.get_node_val(uid,cid)
    parent_score = (cid,scoringFunction(score)) if score else (cid,scoringFunction((0,0,0,0)))
    if cid:
        return propagator(parent_score,child_scores) if child_scores else [parent_score]
    else:
        return child_scores

def propagator(parent_category_score,category_scores):
    number_of_siblings = len(category_scores)
    simple_constant = 0.5 / number_of_siblings
    # print "Parent Category Score: ", parent_category_score
    # print "Child category scores: ", category_scores
    score = sum([x[1] for x in category_scores]) * simple_constant
    try:
        association_coefficient = Category.objects.get(id=parent_category_score[0])
    except:
        association_coefficient = 0
    c_s = [(parent_category_score[0],parent_category_score[1] + score)] + category_scores
    return zip([x[0] for x in c_s],flatten_expo(association_coefficient,[x[1] for x in c_s]))




def normalize(user_CategoryTree):
    

def probabilistic_walk(user_CategoryTree,key="score",parent_score=1.0):
    probability = "probabilistic_walk"

    scores = user_CategoryTree.get_key_value(key)
    for tree in user_CategoryTree.get_children():
        scores+ = tree.get_key_value(key)
    
    count = len(user_CategoryTree.get_children()) + 1
        
    if scores = 0:
        user_CategoryTree.insert_key_value(probability,parent_score/count)
        for tree in user_CategoryTree.get_children():
            tree.insert_key_value(probability,parent_score/count)
    else:
        user_CategoryTree.insert_key_value(probability,parent_score*user_CategoryTree.get_key_value(key)/count)
        for tree in user_CategoryTree.get_children():
            tree.insert_key_value(probability,parent_score *tree.get_key_value(key)/scores)

    for tree in user_Category.get_children(key):
        probabilistic_walk(tree,key,tree.get_key_value(probability)/scores)
    
