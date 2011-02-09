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

#Sew the functions in together
def random_tree_walk_algorithm(user):
    """
    All algorithms follow this same fundamental structure
        Input: User as input 
        N is the number of events to return and has a default of 20 (configured in settings.py)
    Output: Ordered list of EventIDs
    """
    userTree = CategoryTree(user)
    userTree.top_down_recursion(scoring_function,{"outkey":"score"})
    userTree.bottom_up_recursion(topN_function,{"inkey":"score","outkey":"topNscore"})
    #userTree.top_down_recursion(probabilistic_walk,{"inkey":"topNscore", "outkey":"topNscore_probability"})
    userTree.top_down_recursion(topN_score_combinator,{"inkey1":"score", "inkey2":"topNscore", "outkey":"combined_score"})
    userTree.top_down_recursion(probabilistic_walk,{"inkey":"combined_score", "outkey":"combined_probability"})
    #print [(x[0],x[1][0]) for x in userTree.get_category_scores_dictionary(["topN_walk_score","walk_score"])]
    #print "Sum is: ", sum([x[1][0] for x in userTree.get_category_scores_dictionary(["walk_score"])])
    #print "Sum of scores is: ", sum([x[1][0] for x in userTree.get_category_scores_dictionary(["prob_scores"])])
    return SampleDistribution([(x[0],x[1][0]) for x in userTree.get_category_scores_dictionary(["combined_probability"])],settings.N)

def topN_score_combinator(parent,inkey1 = "inkey1", inkey2="inkey2", outkey="combined_score"):
    parent.insert_key_value(outkey, parent.get_key_value(inkey1) * parent.get_key_value(inkey2)) 

"""
Call probabilistic_walk recursively top down on the category tree.
CategoryTree tree
tree.top_down_recursion(probabilistic_walk,dictionary)
Function would look like: 
"""
def probabilistic_walk(parent, inkey, outkey):
    # If this is the Root node, insert a value of 1.0 for probability of parent and score of 0 (so the parent isn't assigned a score: unless all children scores are zero)
    if not parent.get_parent():
        parent.insert_key_value(outkey, 1.0)
        parent.insert_key_value(inkey,0.0)

    children = parent.get_children()

    parent_score = parent.get_key_value(outkey)

    total_score = sum([tree.get_key_value(inkey) for tree in [parent] + children])

    for tree in [parent] + children:
        if not tree.get_parent:
            tree.insert_key_value(outkey,0.0)
        else:
            if total_score:
                tree.insert_key_value(outkey, parent_score * tree.get_key_value(inkey) / total_score)
            else:
                tree.insert_key_value(outkey, parent_score / (len(children) + 1))

"""
#Comment:
topN function should be called bottom up (to ensure niche categories get enough attention)
Example:
CategoryTree tree
tree.bottom_up_recursion(topN_function,dictionary)
"""
def topN_function(parent,inkey="score",outkey="topNscore"):
    if not parent.get_parent():
        parent.insert_key_value(outkey,0.0)
        parent.insert_key_value(inkey,0.0)

    else:
        children = parent.get_children()        
        if not children:
            parent.insert_key_value(outkey,parent.get_key_value(inkey))
            #print "Inserted in", parent.category.id, " ", outkey,": ", parent.get_key_value(outkey)
        else:
            parent.insert_key_value(outkey,settings.top3Score([tree.get_key_value(inkey) for tree in [parent]+children]))
            #parent.insert_key_value(outkey,settings.top3Score([tree.get_key_value(outkey) for tree in children]))
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
    #import pdb; pdb.set_trace()
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

"""
def propagator(parent_category_score,category_scores):
    This function has been deprecated.
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

Trial Functions:
def assign_probabilities(parent, inkey="topNscore", outkey="topN_prob_scores"):
    children = parent.get_children()
    #Calculate total topNscore
    total_top_n_score = sum([tree.get_key_value(inkey) for tree in children])

    if not parent.get_parent():
        parent.insert_key_value(outkey, 1.0)
        #print "inserted 1.0 at root"
        
    for tree in children:
        if total_top_n_score:
            tree.insert_key_value(outkey, parent.get_key_value(outkey) * parent.get_key_value(inkey) / total_top_n_score)
            #print "inserted in ", tree.category.id, " ", parent.get_key_value(outkey) * parent.get_key_value(probability_key) / total_top_n_score
        else:
            tree.insert_key_value(outkey, parent.get_key_value(outkey) / len(children))
            #print "inserted in ", tree.category.id, " ", parent.get_key_value(outkey) / len(children)

def assign_category_probabilities(parent, inkey = "scores", outkey = "cat_prob_scores"):
    parent = parent.get_children()
    total_score = sum([tree.get_key_value(inkey) for tree in [parent] + children])
    for tree in [parent] + children:
        if total_score:
            tree.insert_key_value(outkey, tree.get_key_value(outkey) * tree.get_key_value(inkey) / total_score)
            #print "inserted in ", tree.category.id, " ", tree.get_key_value(outkey) * tree.get_key_value(inkey) / total_score
        else:
            tree.insert_key_value(outkey, tree.get_key_value(outkey)/(len(children)))
            #print "inserted in ", tree.category.id, " ",tree.get_key_value(tree.get_key_value(outkey)/(len(children) + 1))

def score_propagator(user_CategoryTree,inkey="SCORE",outkey="propScore"):
    for tree in user_CategoryTree.get_children():
        propogator(user_categoryTree,inkey,outkey) 
    scores = [user_categoryTree.get_key_value(inkey)] + [tree.get_key_value(inkey) for tree in user_CategoryTree.get_children()]
    user_categoryTree.insert_key_value(outkey,settings.scoreCombinator(list_scores))

def score_algorithm(user, category=None):

    All algorithms follow this same fundamental structure
        Input: User as input 
        N is the number of events to return and has a default of 20 (configured in settings.py)
    Output: Ordered list of EventIDs

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
    
"""
