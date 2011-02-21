"""
 Author: Vikas Menon
 Date: 2/11/2011
 This module contains all the Machine Learning algorithms that get applied to the CategoryTree to generate recommendations.
 All algorithms follow the same fundamental structure:
     a) Required input is a CategoryTree.
     b) Each function works on a parent and its children.
     c) Each function may be applied top_down_recursive or bottom_up_recursive.
     d) Each function only writes to the CategoryTree dictionary.
 The most important (main) function is get_event_recommendations(user) which is called by the middle tier.
 It returns a set of events as recommendations.
 All default values and functions are defined in settings.py.
 #ToDo: Migrate all default values and functions from settings.py into LiveSettings

 Assumptions:
    1) Each event is assigned only a single Concrete category and potentially multiple abstract categories. 
"""

import numpy
import random
import helper
import settings
from events.models import Category, Event
from CategoryTree import CategoryTree
from django.contrib.auth.models import User
from behavior.models import EventActionAggregate
from collections import defaultdict
from itertools import izip

def recommend_events(user, categories=None, N=settings.N):
    if not categories:
        categories = random_tree_walk_algorithm(user, N)

    return filter_events(user, categories, N)


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

    # Flatten the scores to infuse contagiousness
    #userTree.top_down_recursion(flattening_function,{"inkey":"combined_score","outkey":"flattened_score"})

    # Perform a probabilistic walk on the tree generated.
    #userTree.top_down_recursion(probabilistic_walk,{"inkey":"flattened_score", "outkey":"combined_probability"})
    userTree.top_down_recursion(probabilistic_walk,{"inkey":"combined_score", "outkey":"combined_probability"})

    # Useful Debugging statements:
    #print userTree.print_dictionary_key_values()
    #print "Sum of scores is: ", sum([x[1][0] for x in userTree.get_all_category_scores_dictionary(["prob_scores"])])
    return SampleDistribution([(x[0],x[1][0]) for x in userTree.get_all_category_scores_dictionary(["combined_probability"])],N)



def abstract_scoring_function2(user,event):
    """
    This scoring function estimates the score an event recieved based on its abstract categories.
    ToDo: Use a kernel function instead of returning mean.
    """
    scores_list = []
    # Given an event find the "maximum" scores for all categories that are abstract.
    for c in [cat for cat in event.categories.get_query_set() if cat.category_type=='A']:
        try:
            eaa = EventActionAggregate.objects.get(user=user, category=c)
        except:
            #If no score found for this particular user, use default users scores.
            eaa = EventActionAggregate.objects.get(user=settings.get_default_user(), category=c)
        scores_list.append(settings.abstract_scoring_function((eaa.g, eaa.v, eaa.i, eaa.x)))
    if scores_list:
        return sum(scores_list)/len(scores_list)
    return 0

def abstract_scoring_function(user,eid,dictionary_category_eaa, abstract_category_ids):
    """
    This scoring function estimates the score an event recieved based on its abstract categories.
    ToDo: Use a kernel function instead of returning mean.
    """
    scores_list = []
    # Given an event find the "maximum" scores for all categories that are abstract.
    #for c in [cat for cat in Event.objects.get(id=eid).categories.filter(category_type='A')]:
        #scores_list.append(settings.abstract_scoring_function(dictionary_category_eaa[c.id]))

    scores_list = [settings.abstract_scoring_function(dictionary_category_eaa[c]) for c in abstract_category_ids]
    if scores_list:
        score =  sum(scores_list)/len(scores_list)
        #print "Score: ", score
        return score
    return 0

#testing
def filter_events(user,categories=None, N=settings.N, **kwargs):
    """
    Input: User,
           List of categories
           N = Number of recommendations to provide
    Output: List of events.
    Description:
                 This function accepts as input a list of categories and randomly selects 50 events for these categories
                 Events that are cross listed in multiple times have a higher probability of getting selected.
                     - Once selected, they also have a higher probability of getting sampled.
    """
    # ToDo: Filter events that have already been X'd
    # ToDo: This function is a stop-gap solution. We need to sample and score all events optimally.
    # For performance reasons in testing limiting this to 50 events for now.
    
    dictionary = defaultdict(lambda :0)
    num_events = 50  #Should this be a setting?
    for c in categories:
        dictionary[c] += num_events

    events = []
    
    #events = [Event.objects.filter(concrete_category=category).order_by('?')[:number] for category,number in dictionary.iteritems()]
    events = [(category,Event.objects.filter(concrete_category=category).values_list('id').order_by('?')[:number]) for category,number in dictionary.iteritems()]
    #events = [a[0] for b in events for a in b]
    #The events list is of the form: [('cid1', [(eid1,), (eid2,)]), ('cid2', [(eid3,), (eid4,)])]
    #Converting this to [('cid1',['eid1','eid2']),('cid2',['eid3','eid4'])]
    events = [(c, [e[0] for e in elst]) for c, elst in events]
    
    #For all categories:abstract and concrete:
    eaa = EventActionAggregate.objects.filter(user=user)
    dictionary_category_eaa = defaultdict(lambda :(0,0,0,0))
    dictionary_category_eaa = dict((ea.category_id,(ea.g,ea.v,ea.i,ea.x)) for ea in eaa)

    eaa = EventActionAggregate.objects.filter(user=settings.get_default_user())
    defaultdict_category_eaa = dict((ea.category_id,(ea.g,ea.v,ea.i,ea.x)) for ea in eaa)

    #This is inefficient. think of better ways to do it. 
    for k in set(defaultdict_category_eaa.keys()) - set(dictionary_category_eaa.keys()):
        dictionary_category_eaa[k] = defaultdict_category_eaa[k]

    del defaultdict_category_eaa

    ##!! This part takes unreasonably long to complete. Optimize it:
    ##############"
    #import datetime
    #start = datetime.datetime.now()
    #import pdb; pdb.set_trace()
    event_score = defaultdict(lambda :0)
    for category,events in events:
        for event_id,abstract_categories in zip(events,get_categories(events,'A')):
            event_score[event_id] += abstract_scoring_function(user,event_id,dictionary_category_eaa, abstract_categories)
            events += SampleDistribution(event_score.items(),dictionary[c]/50)
            
    #The formatting of events sent to semi sort below ensures that the comparison works. For example: (21,'a') > (12,'b') in python. 
    semi_sorted_events =  semi_sort([(event_score[e],e) for e in events], min(3,len(events)))
    return probabilistic_sort(events)


def semi_sort(events, top_sort=3):
    """
    Since we always have only 20 events, not using any fancy algorithms. Just regular scan and find max 3
    #ToDo: Make more efficient. Use a max heap for efficiency. 
    !Python does not support a max heap. :(
    """
    for i in range(top_sort):
        maximum = events[i]
        pos = i
        for j in range(i+1,len(events)):
            if maximum < events[j]:
                pos = j
                maximum = events[j]

        #Swap maximum with the top i'th position under evaluation.
        events[pos],events[i] = events[i],events[pos]
        
    return events

def probabilistic_sort(events):
    """
    This is an utterly simple probabilistic sort with no guarantees..
    It's purpose is to bubble up preferred elements towards the top of the list.
    """
    for i in range(len(events)):
        a, b = random.randrange(0,len(events)-1), random.randrange(0,len(events)-1)
        if a > b:
            a, b = b, a

        if events[a] < events[b]:
            events[a], events[b] = events[b], events[a]
    return events


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
    This is the recursive scoring function that calculates score based on the GVIX values and stores them in outkey.
    """
    # If this is the root node, insert a value of 0
    #import pdb; pdb.set_trace()
    if not parent.get_parent():
        parent.insert_key_value(outkey,0)
    else:
        parent.insert_key_value(outkey,settings.scoringFunction(parent.get_score()))



def flattening_function(parent, inkey="score", outkey="flattened_score"):
    """
    This is the recursive flattening function.
    """
    if not parent.get_parent():
        flatten_categories = parent.get_children()
    else:
        flatten_categories = [parent] + parent.get_children() 

    outkeys = flatten_expo(parent.association_coefficient(), [x.get_key_value(inkey) for x in flatten_categories])
    for i in range(len(flatten_categories)):
        flatten_categories[i].insert_key_value(outkey,outkeys[i])



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
    Given a distribution of [(item,score)] samples items.
    Items are first normalized by scores and then sampled from it.
    """
    #    Convert into a cumulative distribution
    CDFDistribution = numpy.cumsum(normalize([x[1] for x in distribution]))
    #print "Distribution: ",  CDFDistribution
    returnList = []
    for i in range(trials):
        value = random.random()
        #todo: use binary search to scan the array and locate count faster
        count = 0
        for count in range(len(distribution)):
            if (value < CDFDistribution[count]): break
        if distribution:
            returnList += [(distribution[count])[0]]
    #import pdb; pdb.set_trace()
    return returnList



def get_categories(event_ids=None,categories = 'E'):
    """
    #FIXME: This requires a significant fix.We need to model the ORM effectively here in some way.
    Input: Event_ids, categories which may be 'E' - Everything, 'A' - Abstract or 'C' - Concrete
    Output: List of list of category ids corresponding to Event_ids
    """
    concrete_categories, abstract_categories, all_categories = [], [], []
    #events = Event.objects.select_related('categories').in_bulk(event_ids).values()
    if categories == 'E' or categories == 'C':
        #This also may be optimized with a bulk request for events. 
        concrete_categories =[[e[0]] for e in [Event.objects.values_list('concrete_category_id').get(id=e) for e in event_ids]]
    if categories == 'E' or categories == 'A':
        """
        This part needs serious refactoring.
        """
        import MySQLdb
        conn=MySQLdb.connect(passwd="test",db="abexmid",user="root")
        cursor= conn.cursor()
        format_string = ",".join(['%s'] * len(event_ids))
        
        #values = tuple([str(e) for e in event_ids])
        query = """
        SELECT event_id,category_id
        FROM events_event_categories
        where event_id IN (%s)
        """
        #import pdb; pdb.set_trace()
        cursor.execute(query % format_string,tuple(event_ids))
        dictionary = defaultdict(lambda :[])
        for a,b in cursor.fetchall():
            dictionary[a].append(b)
        abstract_categories = [dictionary[e] for e in event_ids]
        
    #print "abstract_categories: ", abstract_categories
    #print "recommended_categories: ", recommended_categories
    if categories == 'E':
        all_categories = [ i + j for i,j in izip(concrete_categories,abstract_categories)]
        return all_categories
    if categories == 'C':
        return concrete_categories
    else:
        return abstract_categories
    
