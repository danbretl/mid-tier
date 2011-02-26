"""
 Author: Vikas Menon
 Date: 2/11/2011
 This module contains all the Machine Learning algorithms that get applied to -
 the CategoryTree to generate recommendations.
 All algorithms follow the same fundamental structure:
     a) Required input is a CategoryTree.
     b) Each function works on a parent and its children.
     c) Each function may be applied top_down_recursive or bottom_up_recursive.
     d) Each function only writes to the CategoryTree dictionary.
 The most main function is get_event_recommendations(user) which is called by 
 the middle tier.
 It returns a set of events as recommendations.
 All default values and functions are defined in settings.py.
 #ToDo: 
 Migrate all default values and functions from settings.py into LiveSettings

 Assumptions:
    1) Each event is assigned only a single Concrete category and 
       potentially multiple abstract categories.
"""

import numpy
import random
import settings
from events.models import Event, Category, CategoryManager
from CategoryTree import CategoryTree
from behavior.models import EventActionAggregate
from collections import defaultdict
import operator
import math

def recommend_events(user, events=None, categories=None, number=settings.N):
    """
    This is the primary api for the mid-tier to connect to.
    Input: User, Categories (optional) : The list of categories the user is interested in.
    If provided, only 
    number is the number of recommendations requested. This is defaulted to N in settings.py
    """
    categories = defaultdict(lambda :0)
    if not categories:
        categories_dict = random_tree_walk_algorithm(user, number)
    else:
        # When we have multiple categories as input we want to sample them and all their children.
        # We perform a random walk starting on each of the categories. Each of these is going to produce a
        # dictionary of (category,scores). We combine these dictionaries together and then renormalize their scores.
        # Combining dictionaries currently adds up all scores, this might not be the best solution and may require
        # changes depending on performances.
        # Most often, we expect only a single category to get passed, in which case this isn't a concern. 
        categories_dicts = [random_tree_walk_algorithm(user, number/len(categories), category) for category in categories]
        categories = defaultdict(lambda :0)
        for cat_dict in categories_dicts:
            for k,v in cat_dict:
                categories_dict[k] += v

        categories_dict = dict(zip(categories_dict.keys(), normalize(categories_dicts.values())))

    # print "Recommended categories: ",[c.title for c in categories]
    return filter_events(user, events, categories_dict, number)


def recommend_categories(user, number=settings.N, category=None):
    """
    Input:
        a) User:Required
        b) N: Optional. Number of recommendations to generate
        c) Category: Optional. 
                     Recommends all Categories below this Category. 
                     Defaults to the 'Concrete Category'
    Output:
        a) List of recommended Categories (may be repeated)
    """
    return random_tree_walk_algorithm(user, number, category)


def random_tree_walk_algorithm(user, number=settings.N, category=None):
    """
    Input:
        a) User: Required. 
        b) number: Optional. Number of recommendations to generate. 
    Output: Categories with their probability scores.
    """

    # Generate CategoryTree for user
    user_tree = CategoryTree(user, category)

    # Calculate scores for each Category in CategoryTree. 
    # Score is calculated from GVIX.
    # This function can be applied in any order. Top-Down or Bottom-Up.
    # Using Top-Down since it is currently implemented to be tail-recursive and
    # could  be optimized by the compiler.
    user_tree.top_down_recursion(scoring_function, {"outkey":"score"})

    # Apply Top-N function Bottom-Up.
    # Conceptually this gives niche categories the opportunity to bubble 
    # thier scores up through their parent towards the root  and thus
    # increasing chances of the parent getting selected,and effectively
    # maximizing their own chance of getting selected. 
    # This will increase exploitativeness.
    user_tree.bottom_up_recursion(topn_function, {"inkey":"score", 
                                                 "outkey":"topNscore"})

    # This is a modification of the Top-N algorithm. 
    # When scores get bubbled up via parents, the probability of parents 
    # getting selected also goes up proportionally. 
    # This function normalizes the score of a parent and makes it proportional
    # to its GVIX score, 
    # Currently combining the two multiplicatively.
    user_tree.top_down_recursion(score_combinator, {"inkey1":"score", 
                                                   "inkey2":"topNscore", 
                                                   "outkey":"combined_score"})

    # Flatten the scores to infuse contagiousness
    user_tree.top_down_recursion(flattening_function, {"inkey":"combined_score", 
                                                      "outkey":"flattened_score"})

    # TRIAL:
    # import pdb; pdb.set_trace()
    user_tree.top_down_recursion(depth_assignment, {"outkey":"depth"})
    # print userTree.get_all_category_scores_dictionary(["depth",
    #                                                   "flattened_score"])
    # import pdb; pdb.set_trace()
    user_tree.top_down_recursion(score_combinator, {"inkey1":"depth",
                                                   "inkey2":"flattened_score",
                                                   "outkey":"dscore"})

    #category_count = get_real_time_category_count(user)
    #user_tree.top_down_recursion(score_multiplier,{"inkey":"score","function_of_parent":(lambda x: category_count[x]), "outkey":"multiplied_score"})
    
    user_tree.top_down_recursion(probabilistic_walk, {"inkey":"dscore",
                                                     "outkey":"combined_probability"})

    # Testing material here:
    # absd = dict([(c.title, p[0]) for c, p in 
    #             userTree.get_all_category_scores_dictionary(["score"])
    # print "Scores:",sorted(absd.iteritems(), key=operator.itemgetter(1))[-5:]


    # Useful Debugging statements:
    # print userTree.print_dictionary_key_values()

    #return sample_distribution([(x[0], x[1][0]) for x in 
    #                            user_tree.get_all_category_scores_dictionary(["combined_probability"])], number)
    category_id_scores = [(x[0], x[1][0]) for x in user_tree.get_all_category_scores_dictionary(["combined_probability"])]
    return dict(zip([x[0] for x in category_id_scores],normalize([x[1] for x in category_id_scores])))


def abstract_scoring_function(abstract_category_ids, dictionary_category_eaa):
    """
    This scoring function estimates the score an event recieved based 
    on its abstract categories.The abstract categories are passed as input with a dicitonary
    that maintains the mapping between the scores and the category. 
    ToDo: Use a kernel function instead of returning mean.
    """
    scores_list = []

    scores_list = [settings.abstract_scoring_function(dictionary_category_eaa[c]) for c in abstract_category_ids]

    if scores_list:
        score =  sum(scores_list) / len(scores_list)  #mean
        # print "Score: ", score
        return score
    return 0


def generate_category_mapping(event_query_set=None, categories_dict=None):
    """
    Input: a) Query set of event objects
           b) List of cateegories with probability scores.
    Output:
           default dictionary category_event_map[category] = list of event ids. 
    """
    #import time
    #start = time.time()
    category_event_map = defaultdict(lambda: [])

    #This is an optimization. 
    #Load all category objects into a dictionary. 
    all_category_dict = dict([(category.id,category) for category in Category.objects.filter(category_type='C')])

    if not event_query_set:
        # events stores categories and event ids corresponding to that category
        event_ids = [(category, Event.objects.filter(concrete_category=category).values_list('id'))
                  for category, number in sorted(categories_dict.iteritems(),key=operator.itemgetter(1))[-50:]]

        #This is an optimization. 
        #Load all category objects into a dictionary. 
        all_category_objs = Category.objects.filter(category_type='C')
        all_category_dict = dict([(category.id,category) for category in all_category_objs])

        # events = [a[0] for b in events for a in b]
        # The events list input is of the form: 
        #              [('cid1', [(eid1,), (eid2,)]), ('cid2', [(eid3,), (eid4,)])]
        # Converting this to [('cid1',['eid1','eid2']),('cid2',['eid3','eid4'])]
        for category, event in [(category, [eid[0] for eid in elst]) for category, elst in event_ids]:
            category_event_map[category] +=event
    else:
        #for category,event in [(e_obj.concrete_category, e_obj.id) for e_obj in event_query_set]:
        #    category_event_map[category].append(event)
        categoryid_event_map = defaultdict(lambda :[])
        for category, event in event_query_set.values_list('concrete_category_id','id'):
            categoryid_event_map[category].append(event)

        for category_id in categoryid_event_map.keys():
            category = all_category_dict[category_id]
            category_event_map[category] = categoryid_event_map[category_id]
    #print "Time taken: ", time.time() - start
    return category_event_map


def filter_events(user, event_query_set=None, categories_dict=None, number=settings.N):
    """
    Input: User,
           List of categories
           N = Number of recommendations to provide
    Output: List of events.
    Description:
                 This function accepts as input a list of categories and
                 randomly selects 50 events for these categories
                 Events that are cross listed in multiple concrete categories
                 have a higher probability of getting selected.
                 Once selected, they also have a higher probability
                 of getting sampled.
    """
    # ToDo: Filter events that have already been X'd
    # For performance reasons in testing limiting this to 50 events for now.
    # The hope is that geo-location based filtering will also roughly break
    # down the number of events down to roughly 50 a category.
    
    #events = [Event.objects.filter(concrete_category=category).order_by('?')[:number]
    #          for category,number in dictionary.iteritems()]
    # Should the number 50 be a setting?

    events = generate_category_mapping(event_query_set,categories_dict)
    event_dictionary = dict()


    # Remove all categories that are not present in the set of events so we only sample categories for which we have events. 
    for key in set(categories_dict.keys()) - set(events.keys()):
            del categories_dict[key]
    categories = sample_distribution(categories_dict.items(), settings.N)
    
    # This is an optimization.
    # Prepare in advance all the users behavior for the categories under consideration. 
    eaa = EventActionAggregate.objects.filter(user=user,category__in=categories)
    dictionary_category_eaa = defaultdict(lambda :(0, 0, 0, 0))
    for ea in eaa:
        dictionary_category_eaa[ea.category_id] = (ea.g, ea.v, ea.i, ea.x)

    # This contains the selected events to be returned. 
    selected_events = []

    #This is an optimization
    #Stores the score for every event id.
    event_abstract_score = defaultdict(lambda :0)
    for category, event_ids in events.iteritems():
        #Mapping between event ids and all abstract categories.
        event_cat_dict = get_categories(event_ids, 'A')
        for event_id, abstract_categories in event_cat_dict.items():
            event_abstract_score[event_id] += abstract_scoring_function(abstract_categories, dictionary_category_eaa)

    # First sample a category (already sampled and available in categories).
    # This maintains a count of all categories that were sampled from but didn't have enough events and need to be asked for again. 
    missing_count = 0
    for category in categories:
        # Next sample an event based on the abstract score.
        event = sample_distribution([(event_id, event_abstract_score[category]) for event_id in events[category]])
        if event:
            selected_events += event
            # This ensures an already selected event does not get selected again.
            events[category] = list( set(events[category]) - set(list(event)))
        else:
            #This category has no more events. If it comes down to it, Don't sample it ever again.
            try:
                del categories_dict[category]
            except:
                #There are no more events.Period.
                break
            missing_count += 1
        #Fixme: Inefficient.

        if len(events[category]) == 0 :
            del events[category]
            

    if missing_count > 0 and len(events) > 0:
        # This is "hopefully" unlikely to happen if there are enough events in each category.
        # If we get to this point, it means we don't have enough events for the categories sampled
        # resample from the categories and recommend more events. This is one place where we could break the settings.max_probability cap.
        # But this could be necessary for example if you are in Waukeesha, Wisconsin and only have movies to go to.
        # Or worse, if you are in Wahkon, Wisconsin and have no events or literally  nothing around you. 
        selected_events += filter_events(user,event_query_set, categories_dict,missing_count)
        
    # The formatting of events sent to semi sort below ensures that the comparison works. For example: (21,'a') > (12,'b') in python. 
    selected_events =  semi_sort([(event_abstract_score[eid], eid) for eid in selected_events], min(3, len(selected_events)))

    # print "Number of events recommended: ", len(selected_events)
    #print fuzzy_sort(selected_events)
    if event_query_set:
        return [event_query_set.get(id=event_id) for event_id in fuzzy_sort(selected_events)]
    else:
        return [Event.objects.get(id=event_id) for event_id in fuzzy_sort(selected_events)]


def semi_sort(events, top_sort=3):
    """
    This function sorts [(event_score,event)]* 
    such the the events with the top top_sort (say 3) scores
    are always listed first.The rest of the events are not sorted 
    in any manner.

    Since we always have only 20 events, not using any fancy 
    algorithms for semi-sort. 
    
    Time-Complexity is proportional to O(top_sort * len(events)) 
    where top_sort has an upper bound of len(events)
    
    ToDo: Nice to have: Make this more efficient. 
    Use a max heap for efficiency. Efficiency would then be 
    O(log(top_sort)*len(events))
    
    Note:Python does not support a max heap by default 
         (maybe use a min heap with -ve values for keys) :(
    """
    for i in range(top_sort):
        maximum = events[i]
        pos = i
        for j in range(i+1, len(events)):
            if maximum < events[j]:
                pos = j
                maximum = events[j]

        # Swap maximum with the top i'th position under evaluation.
        events[pos], events[i] = events[i], events[pos]
        
    return events

def fuzzy_sort(events):
    """
    This function recieves [(event_score,event)]* as input and a 
    roughly better sorted list.
    This is a simple probabilistic sort with no guarantees.
    It's purpose is to bubble up preferred elements towards 
    the top of the list.
    """
    for index in range(len(events)):
        item1 = random.randrange(0, len(events) - 1)
        item2 = random.randrange(0, len(events) - 1)
        if item1 > item2:
            item1, item2 = item2, item1

        if events[item1] < events[item2]:
            events[item1], events[item2] = events[item2], events[item1]
    return [ev[1] for ev in events]


def score_combinator(parent, inkey1, inkey2, outkey):
    """
    Multiplies inkey1 and inkey2 and stores the result in outkey in the 
    dictionary.
    Input:
         Parent (required)
         Inkey1 (required)
         Inkey2 (required)
         Outkey (required)
    
    """
    try:
        parent.insert_key_value(outkey, parent.get_key_value(inkey1) * 
                                parent.get_key_value(inkey2))
    except:
        # Should be instead throwing an exception here. 
        # ToDo: Define exceptions of machine learning algorithms.
        print "Score combination failed for ", parent.title


#usage: user_tree.top_down_recursion(score_multiplier,{"inkey":"score","function_of_parent":(lambda x: category_count[x]), "outkey":"multiplied_score"})
def score_multiplier(parent,inkey,function_of_parent,outkey):
    try:
        parent.insert_key_value(outkey, parent.get_key_value(inkey) * function_of_parent(parent))
    except:
        print "Score multiplication failed for ", parent.title


def probabilistic_walk(parent, inkey, outkey):
    """
    A probabilistic walk can be performed on any key on the dictionary 
    if and only if the key stores non-negative values.
    Conceptually, the walk is such that the probability of reaching a parent 
    gets divided amongst itself and all its children.
    The loop invariants are thus:
        a) After a loop, the Sum of scores of all children and parent 
           sum up to the original score of the parent.
        b) At any given point in the walk, the sum of all scores add up to 1.0
          (This is also a necessary requirement for Sampling)
    The parent root node always starts with a probability of 1.0.
    Every node is assigned a positive probability if it has a postive inkey, 
    unless (if and only if) it is the root node
    """
    if not parent.get_parent():
        parent.insert_key_value(outkey, 1.0)
        # This ensures that the Root node is assigned a probability of 0.0 
        # and hence never selected during sampling.
        parent.insert_key_value(inkey, 0.0)

    children = parent.get_children()

    # The parent outkey will always be assigned before this step. 
    # Why? Because this is top down recursion starting from the root,
    # which has a score of 1.0. In the next steps all the children 
    # will have their outkey assigned.
    parent_out_score = parent.get_key_value(outkey) * 1.0

    # Calculate the total of all children and parent based on the inkey. 
    # Why? Because the walk is performed based on the inkey values.
    scores = [tree.get_key_value(inkey) for tree in [parent] + children]
    total_in_score = sum(scores)

    # Reassign probabilities to the parent based on the distribution 
    # of its children and assign probabilities to all children.
    for tree in [parent] + children:
        if total_in_score:
            score = tree.get_key_value(inkey)
            score = parent_out_score * score / total_in_score
            tree.insert_key_value(outkey, score)
        else:
            tree.insert_key_value(outkey, 
                                  parent_out_score / (len(children) + 1))


def topn_function(parent, inkey="score", outkey="topNscore"):
    """
    This function gets applied bottom_up_recursively on a CategoryTree
    It calculates the mean of the top k inkey scores amongst a parent and 
    all its children and stores it in outkey
    """
    if not parent.get_parent():
        parent.insert_key_value(outkey, 0.0)
        parent.insert_key_value(inkey, 0.0)

    else:
        children = parent.get_children()        
        if not children:
            parent.insert_key_value(outkey, parent.get_key_value(inkey))
        else:
            score = [tree.get_key_value(inkey) for tree in [parent] + children]
            parent.insert_key_value(outkey, settings.top3Score(score))


def scoring_function(parent, outkey="score"):
    """
    This function calculates score based on the GVIX values 
    and stores them in outkey.
    """
    # If this is the root node, insert a value of 0
    # import pdb; pdb.set_trace()
    if not parent.get_parent():
        parent.insert_key_value(outkey, 0)
    else:
        score = settings.scoringFunction(parent.get_score())
        parent.insert_key_value(outkey, score)


def depth_assignment(parent, outkey):
    """
    Assigns the depth of the node from the root. 
    """
    if not parent.get_parent():
        parent.insert_key_value(outkey, 0)
    
    in_value = parent.get_key_value(outkey) + 1
    in_value = in_value * in_value * in_value 
    if in_value:
        for tree in parent.get_children():
            tree.insert_key_value(outkey, in_value)



def flattening_function(parent, inkey="score", outkey="flattened_score"):
    """
    This is the recursive flattening function.
    It introduces the contagiousness between neighbours.
    """
    if not parent.get_parent():
        flatten_categories = parent.get_children()
        parent.insert_key_value(outkey, 0.0)
    else:
        flatten_categories = [parent] + parent.get_children()

    scores = [x.get_key_value(inkey) for x in flatten_categories]
    outkeys = flatten_expo(0.2, scores)

    for i in range(len(flatten_categories)):
        flatten_categories[i].insert_key_value(outkey, outkeys[i])


def normalize(lst):
    """
    Normalize a list of numbers so they add up to 1.
    All elements of the list are expected to be zero or positive.
    """
    # If input is empty, return an empty list 
    if not lst: 
        return lst

    # Calculate sum: If the sums adds up to 0, 
    #                  then this is a uniform distribution
    #                Otherwise, return the normalized value for each element.
    total_sum = float(sum(lst))
    if total_sum != 0:
        return [e / total_sum for e in lst]
    else:
        return [1/len(lst) for e in lst]


def decrease(association_coefficient, difference):
    """
    Decrease d by a factor that is smaller and smaller 
    the greater the difference is
    """
    # limit
    if association_coefficient == 0:
        return difference
    return difference * (1 - math.exp(- difference / association_coefficient))


def flatten_expo(association_coefficient, lst):
    """
    Remove part of the distance towards the mean
    The greater the distance from the mean, the lesser the change.
    The flattening coefficient is any number between 0 and infinity.
    """
    mean = sum(lst) / float(len(lst))  # mean
    
    newlst = []
    for item in lst:
        if item > mean:
            newlst.append(mean + decrease(association_coefficient, item-mean))
        else:
            newlst.append(mean-decrease(association_coefficient, mean-item))
    return newlst


def sample_distribution(distribution, trials=1, category_count=None):
    """
    Given a distribution of [(item,score)] samples items.
    Items are first normalized by scores and then sampled from it.
    """
    #    Convert into a cumulative distribution
    cumulative_distribution = numpy.cumsum(normalize([x[1] for x in distribution]))
    # print "Distribution: ",  CDFDistribution
    return_list = []
    if not category_count:
        category_count = defaultdict(lambda : 0)
    for i in range(trials):
        value = random.random()

        # Todo: use binary search to scan the array and locate count faster
        count = 0
        
        for count in range(len(distribution)):
            if (value < cumulative_distribution[count]): 
                break
            
        if distribution:
            if category_count[(distribution[count])[0]] <= (
                trials * settings.max_probability
                ):
                return_list += [(distribution[count])[0]]
                category_count[(distribution[count])[0]] += 1
            else:
                if len(distribution) > 1:
                    del distribution[count]
                else:
                    category_count[(distribution[count])[0]] -=1
                return_list += sample_distribution(distribution,
                                                 trials-i,
                                                 category_count)
                break
                
    # import pdb; pdb.set_trace()
    return return_list


def get_categories(event_ids=None, categories='E'):
    """
    Input: Event_ids, categories which may be 
    'E' - Everything, 'A' - Abstract or 'C' - Concrete
    Output: Dictionary of events corresponding to list of category ids 
    """
    category_manager = CategoryManager()
    eid_categories = None
    if categories == 'E':
        eid_categories = category_manager.for_events(event_ids, 'AC')
    elif categories == 'A':
        eid_categories = category_manager.for_events(event_ids, 'A')
    elif categories == 'C':
        eid_categories = category_manager.for_events(event_ids, 'C')
    else:
        print "Invalid input to function ml.get_categories."

    return eid_categories
