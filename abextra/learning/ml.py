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
from CategoryTree import CategoryTree

def recommend_categories(user):
    return random_tree_walk_algorithm(user)

def recommend_categories_only_subchildren(user, category):
    return random_tree_walk_algorithm(user, category)

def score_algorithm(user, category=None):
    """
    All algorithms follow this same fundamental structure
        Input: User as input 
        N is the number of events to return and has a default of 20 (configured in settings.py)
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
    return SampleDistribution(Normalized_Scores, settings.N)

#Sew the functions in together
def random_tree_walk_algorithm(user):
    userTree = CategoryTree(user)
    scoring_function(userTree)
    probabilistic_walk(userTree)
    return SampleDistribution([(x[0],x[1][0]) for x in userTree.get_category_scores_dictionary(["probabilistic_walk"])],settings.N)

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

def probabilistic_walk(user_CategoryTree,inkey="score",mid_leaf_score="mkey", outkey="probabilistic_walk", parent_score=1.0):
    sum_scores = user_CategoryTree.get_key_value(inkey) 
    sum_scores+= sum ([tree.get_key_value(inkey) for tree in user_CategoryTree.get_children()])
    #print user_CategoryTree.title
    #print "Sum of scores: ",sum_scores
    count = len(user_CategoryTree.get_children()) + 1
    #print "Number of Children: ", count    
    #print "Parent score: ",parent_score
    user_CategoryTree.insert_key_value(mid_leaf_score,user_CategoryTree.get_key_value(outkey))
    if sum_scores == 0:
        user_CategoryTree.insert_key_value(outkey,parent_score/count)
        for tree in user_CategoryTree.get_children():
            tree.insert_key_value(outkey,parent_score/count)
    else:
        user_CategoryTree.insert_key_value(outkey,parent_score*user_CategoryTree.get_key_value(inkey)/sum_scores)
        test_total = user_CategoryTree.get_key_value(outkey)
        for tree in user_CategoryTree.get_children():
            tree.insert_key_value(outkey,parent_score *tree.get_key_value(inkey)/sum_scores)
            #print "Value inserted in ", tree.title," : ",tree.get_key_value(outkey)
            test_total +=tree.get_key_value(outkey)
        #print "Total inserted: ", test_total

    for tree in user_CategoryTree.get_children():
        probabilistic_walk(tree,inkey,mid_leaf_score, outkey,tree.get_key_value(outkey))
    
def score_propagator(user_CategoryTree,inkey="SCORE",outkey="propScore"):
    for tree in user_CategoryTree.get_children():
        propogator(user_categoryTree,inkey,outkey) 
    scores = [user_categoryTree.get_key_value(inkey)] + [tree.get_key_value(inkey) for tree in user_CategoryTree.get_children()]
    user_categoryTree.insert_key_value(outkey,settings.scoreCombinator(list_scores))

def scoring_function(user_CategoryTree,outkey="score"):
    if user_CategoryTree.title == "ROOT": user_CategoryTree.insert_key_value(outkey,0)
    for tree in user_CategoryTree.get_children():
        tree.insert_key_value(outkey,settings.scoringFunction(tree.get_score()))
    for tree in user_CategoryTree.get_children():
        scoring_function(tree,outkey)
