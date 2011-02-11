"""
 Author: Vikas Menon
 Date: 2/11/2011
 This module contains all the Machine Learning algorithms that get applied to the CategoryTree to generate recommendations.
 All algorithms follow the same fundamental structure:
     a) Required input is a CategoryTree.
     b) Each function works on a parent and its children.
     c) Each function may be applied top_down_recursive or bottom_up_recursive.
     d) Each function only writes to the CategoryTree dictionary.
 The most important (main) function is recomend_categories(user) which is called by the middle tier.
 It returns a default number of recommendations.
 All default values and functions are defined in settings.py.
 #ToDo: Migrate all default values and functions from settings.py into LiveSettings
"""

import numpy
import random
import helper
import settings
from events.models import Category
from CategoryTree import CategoryTree

def recommend_categories(user, N=settings.N, category=None):
    """
    Input:
        a) User:Required
        b) N: Optional. Number of recommendations to generate
        c) Category: Optional. Recommends all Categories below this Category. Defaults to the 'Concrete Category'
    Output:
        a) List of recommended Categories (may be repeated)
    """
    return random_tree_walk_algorithm(user, N, category)

#Sew the functions in together
def random_tree_walk_algorithm(user, N=settings.N, category=None):
    """
    Input:
        a) User: Required. 
        b) N: Optional. Number of recommendations to generate. 
    Output: List of recommended categories (may be repeated).
    
    ToDo: Flattening of scores amongst siblings.
    """

    # Generate CategoryTree for user
    userTree = CategoryTree(user,category)

    # Calculate scores for each Category in CategoryTree. Score is calculated from GVIX.
    # This function can be applied in any order. Top-Down or Bottom-Up.
    # Using Top-Down since it is currently implemented to be tail-recursive and can be optimized by the compiler.
    userTree.top_down_recursion(scoring_function,{"outkey":"score"})

    # Apply Top-N function Bottom-Up.
    # Conceptually this gives niche categories to bubble thier scores up through their parent towards the root increasing chances of -
    # the parent getting selected and thus maximising exploitativeness.
    userTree.bottom_up_recursion(topN_function,{"inkey":"score","outkey":"topNscore"})

    # This is a modification of the Top-N algorithm. When scores get bubbled up via parents, the probability of parents getting selected -
    # also goes up proportionally. To make the score of the parent proportional to its GVIX score, we combine the two multiplicatively.
    userTree.top_down_recursion(score_combinator,{"inkey1":"score", "inkey2":"topNscore", "outkey":"combined_score"})

    # Perform a probabilistic walk on the tree generated.
    userTree.top_down_recursion(probabilistic_walk,{"inkey":"combined_score", "outkey":"combined_probability"})

    # Useful Debugging statements:
    #print userTree.print_dictionary_key_values()
    #print "Sum of scores is: ", sum([x[1][0] for x in userTree.get_all_category_scores_dictionary(["prob_scores"])])
    return SampleDistribution([(x[0],x[1][0]) for x in userTree.get_all_category_scores_dictionary(["combined_probability"])],N)


def score_combinator(parent,inkey1, inkey2, outkey):
    """
    Multiplies inkey1 and inkey2 and stores the result in outkey in the dictionary.
    Input:
         Parent (required)
         Inkey1 (required)
         Inkey2 (required)
         Outkey (required)
    
    """
    parent.insert_key_value(outkey, parent.get_key_value(inkey1) * parent.get_key_value(inkey2)) 


def probabilistic_walk(parent, inkey, outkey):
    """
    The probabilistic walk can be performed on any key on the dictionary if and only if the key stores non-negative values.
    Conceptually, the walk is such that the probability of reaching the Parent gets divided amongst itself and all its children.
    The loop invariants are thus:
        a) After a loop, the Sum of scores of all children and parent sum up to the original score of the parent.
        b) At any given point in the walk, the sum of all scores add up to 1.0 (This is also a necessary requirement for Sampling)
    The parent node always starts with a probability of 1.0.
    The parent is assigned a probability, unless (if and only if) it is the root 'Concrete' node
    """
    if not parent.get_parent():
        parent.insert_key_value(outkey, 1.0)
        # This ensures that the Root node is assigned a probability of 0.0 and hence never selected.
        parent.insert_key_value(inkey,0.0)

    children = parent.get_children()

    # The parent outkey will always be assigned before this step. Why? Because this is top down recursion starting from the root,
    # which has a score of 1.0. In the next few steps you will see all the children have their outkey assigned.
    parent_out_score = parent.get_key_value(outkey)

    # Calculate the total of all children and parent based on the inkey. Why? Because the walk is performed based on the inkey values.
    total_in_score = sum([tree.get_key_value(inkey) for tree in [parent] + children])

    # Reassign probabilities to the parent based on the distribution of its children and assign probabilities to all children.
    for tree in [parent] + children:
        if total_in_score:
            tree.insert_key_value(outkey, parent_out_score * tree.get_key_value(inkey) / total_in_score)
        else:
            tree.insert_key_value(outkey, parent_out_score / (len(children) + 1))


def topN_function(parent,inkey="score",outkey="topNscore"):
    """
    This function calculates the mean of the top k inkey scores amongst a parent and all its children and stores it in outkey
    """
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

def scoring_function(parent, outkey="score"):
    """
    
    """
    # If this is the root node, insert a value of 0
    #import pdb; pdb.set_trace()
    if not parent.get_parent():
        parent.insert_key_value(outkey,0)
    else:
        parent.insert_key_value(outkey,settings.scoringFunction(parent.get_score()))


def normalize(lst):
    """
    Normalize all values so they add up to 1.
    All elements of the list are expected to be zero or positive.
    """

    #If input is empty, return an empty list 
    if not lst: return lst

    #Calculate sum: If the sums adds up to 0, then this is a uniform distribution
    #               Otherwise, return the normalized value for each element.
    s = float(sum(lst))
    if s!=0:
        return [e / s for e in lst]
    else:
        return [1/len(lst) for e in lst]

def decrease(x, d):
    """
    Decrease d by a factor that is smaller and smaller the greater the difference is
    """
    # limit
    if x == 0:
        return d
    return d * (1 - math.exp(-d/x))

def flatten_expo(x, lst):
    """
    Remove part of the distance towards the mean
    """
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
    Given a distribution of [(item,probability)] samples items. 
    """
    #    Convert into a cumulative distribution
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

