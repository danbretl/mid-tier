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
    #scoring_function(userTree)
    userTree.top_down_recursion(scoring_function,{"outkey":"score"})
    #topN_function(userTree)
    userTree.bottom_up_recursion(topN_function,{"inkey":"score","outkey":"topNscore"})
    print userTree.get_category_scores_dictionary(["score","topNscore"])
    import pdb; pdb.set_trace()    
    #probabilistic_walk(userTree)
    userTree.top_down_recursion(probabilistic_walk,{"probability_key":"topNscore","inkey":"score", "outkey":"probabilistic_walk"})
    #print [(x[0],x[1][0]) for x in userTree.get_category_scores_dictionary(["probabilistic_walk"])]
    print userTree.get_category_scores_dictionary(["score","topNscore","probabilistic_walk"])
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
    """ normalize all values so they add up to 1.
    All elements of the list are expected to be zero or positive.
    If input is empty, return an empty list """
    if not lst: return lst
    """ Calculate sum.
    If the sums up to 0, then this is a uniform distribution
    Otherwise, return the normalized value for each element.
    """
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
    """
    convert into a cumulative distribution
    """
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
    """ This function has been deprecated."""
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


##Outdated
def probabilistic_walk_deprecated(user_CategoryTree,inkey="topNscore", mid_leaf_score="mkey", outkey="probabilistic_walk", parent_score=1.0):
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

"""
Call probabilistic_walk recursively top down on the category tree.
CategoryTree tree
tree.top_down_recursion(probabilistic_walk,dictionary)
Function would look like: 
"""
def probabilistic_walk(parent, inkey="score", outkey="probabilistic_walk", probability_key = "topNscore"):
    children = parent.get_children()
    mkey = "m." + outkey
    
    #Calculate total topNscore
    total_top_n_score = sum([tree.get_key_value(probability_key) for tree in children])
    print "Total top N score: ", total_top_n_score

    if not parent.get_parent():
        parent.insert_key_value(outkey, 1.0)

    for tree in children:
        if total_top_n_score:
            tree.insert_key_value(outkey, parent.get_key_value(outkey) * parent.get_key_value(probability_key) / total_top_n_score)
        else:
            tree.insert_key_value(outkey, parent.get_key_value(outkey) / len(children))
    
    total_score = sum([tree.get_key_value(inkey) for tree in [parent] + children])
    for tree in [parent] + children:
        if total_score:
            tree.insert_key_value(outkey, tree.get_key_value(outkey) * tree.get_key_value(inkey) / total_score)
        else:
            tree.insert_key_value(outkey, tree.get_key_value(tree.get_key_value(outkey)/(len(children) + 1)))
    

def assign_independent_probabilities(parent, inkey="topNscore", outkey="top_n_probabilities"):
    children = parent.get_children()
    sum_scores = parent.get_key_value(inkey)
    sum_scores += sum([tree.get_key_value(inkey) for tree in children])
    count = len(children) + 1

    # Assign probability walk scores        
    if sum_scores == 0:
        uniform_distribution = 1.0 / count
        parent.insert_key_value(outkey, uniform_distribution )
        for tree in children:
            tree.insert_key_value(outkey, uniform_distribution)
    else:
        parent_score = parent.get_key_value(inkey)
        if not parent_score: parent_score = 0.0
        parent.insert_key_value(outkey, parent_score / sum_scores)
        for tree in children:
            tree.insert_key_value(midleaf_tag, tree.get_key_value(inkey) / sum_scores)


##Outdated
def score_propagator(user_CategoryTree,inkey="SCORE",outkey="propScore"):
    for tree in user_CategoryTree.get_children():
        propogator(user_categoryTree,inkey,outkey) 
    scores = [user_categoryTree.get_key_value(inkey)] + [tree.get_key_value(inkey) for tree in user_CategoryTree.get_children()]
    user_categoryTree.insert_key_value(outkey,settings.scoreCombinator(list_scores))


"""
topN function should be called bottom up (to ensure niche categories get enough attention)
Example:
CategoryTree tree
tree.bottom_up_recursion(topN_function,dictionary)
"""
def topN_function(parent,inkey="score",outkey="topNscore"):
    children = parent.get_children()
    if not children:
        parent.insert_key_value(outkey,parent.get_key_value(inkey))
        #print "Inserted in", parent.category.id, " ", outkey,": ", parent.get_key_value(outkey)
    else:
        parent.insert_key_value(outkey,settings.top3Score([parent.get_category_score_dictionary(inkey)]+[tree.get_category_score_dictionary(inkey) for tree in children]))
        #print "Inserted in", parent.category.id, " ", outkey,": ", parent.get_key_value(outkey)

    

"""
The scoring function works on one node at a time calculating and storing information into the dictionary.
Example:
CategoryTree tree
tree.top_down_recursion(scoring_function,dictionary)
"""
def scoring_function(parent, outkey="score"):
    # If this is the root node, insert a value of 0
    #import pdb; pdb.set_trace()
    if not parent.get_parent():
        parent.insert_key_value(outkey,0)
    else:
        parent.insert_key_value(outkey,settings.scoringFunction(parent.get_score()))
