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
 The most main function is get_event_recommendations(user) which is called by.
 the middle tier.
 It returns a set of events as recommendations.
 All default values and functions are defined in settings.py.
 #ToDo:
 Migrate all default values and functions from settings.py into LiveSettings

 Assumptions:
    1) Each event is assigned only a single Concrete category and
       potentially multiple abstract categories.
"""

from collections import defaultdict
import math
import numpy
from bisect import bisect_left
import random
import settings
from events.models import Category
from events.utils import CachedCategoryTree
from category_tree import CategoryTree
import user_behavior

DJANGO_DB = user_behavior.UserBehaviorDjangoDB()

def recommend_events(user, events=None, number=settings.N):
    """
    This is the primary api for the mid-tier to connect to.
    Input: User, query set representing events to be recommended from.
    If provided, only number is the number of recommendations requested.
        - This is defaulted to N in settings.py
    """
    categories_dict = random_tree_walk_algorithm(user)
    # A list of all categories and their scores.
    #Debugging statements
    # print "Recommended categories: ",[c.title for c in categories]
    # print len(filter_events(user, events, categories_dict, number))
    # t = filter_events(user, events, categories_dict, number, set())
    # import pdb; pdb.set_trace()
    return filter_events(user, events, categories_dict, number, set())

# NOTE: What is the purpose of this wrapper function?
# vikas - Loose coupling. Pasha wanted a fixed api that wouldn't change and
#         would wrap around the machine learning logic.

def recommend_categories(*args, **kwargs):
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
    return random_tree_walk_algorithm(*args, **kwargs)


def random_tree_walk_algorithm(user, category=None, ctree=None, db=DJANGO_DB):
    """
    Input:
        a) User: Required.
        b) number: Optional. Number of recommendations to generate.
    Output: Categories with their probability scores.
    """

    # Generate CategoryTree for user
    user_tree = CategoryTree(user, category, ctree=ctree, behavior_db=db)

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
    # user_tree.top_down_recursion(score_multiplier,{"inkey":"score",
    #                                                "function_of_parent":(lambda x: category_count[x]),
    #                                                "outkey":"multiplied_score"})

    user_tree.top_down_recursion(probabilistic_walk, {"inkey":"dscore",
                                                     "outkey":"combined_probability"})

    # Testing material here:
    # absd = dict([(c.title, p[0]) for c, p in
    #             userTree.get_all_category_scores_dictionary(["score"])
    # print "Scores:",sorted(absd.iteritems(), key=operator.itemgetter(1))[-5:]


    # Useful Debugging statements:
    # print userTree.print_dictionary_key_values()

    #return sample_category_distribution([(x[0], x[1][0]) for x in
    #                            user_tree.get_all_category_scores_dictionary(["combined_probability"])], number)
    category_id_scores = [(x[0], x[1][0]) for x in user_tree.get_all_category_scores_dictionary(["combined_probability"])]
    return dict(zip([x[0] for x in category_id_scores], normalize([x[1] for x in category_id_scores])))


def abstract_scoring_function(abstract_category_ids, dictionary_category_eaa):
    """
    This scoring function estimates the score an event recieved based
    on its abstract categories.The abstract categories are passed as input with a dicitonary
    that maintains the mapping between the scores and the category.
    ToDo: Use a kernel function instead of returning mean.
    ToDo: Do the tree walk to calculate a abstract categories score.
    """
    scores_list = [settings.abstract_scoring_function(dictionary_category_eaa[c]) for c in abstract_category_ids]

    if scores_list:
        score =  sum(scores_list) / len(scores_list)  #mean
        # print "Score: ", score
        return score
    return 0


def generate_category_mapping(event_query_set, categories_dict=None):
    """
    ! This function is for use only with concrete categories.
    Input: a) Query set of event objects
           b) Dictionary of category objects mapping to scores.(optional)
    Output:
           dictionary category_event_map[category object] = set of event ids.
    """
    # This is a dictionary of the form:
    # categoryid_event_map[category id] = list(event ids)
    categoryid_event_map = defaultdict(lambda :[])
    for categoryid, event in event_query_set.values_list('concrete_category_id','id'):
        categoryid_event_map[categoryid].append(event)

    if not categories_dict:
        all_category_dict = dict([(category.id, category)
                                  for category in
                                  Category.objects.filter(category_type='C')])
    else:
        all_category_dict = dict([(category.id, category)
                                  for category in categories_dict.keys()])

    # This is a dictionary of the form:
    # category_event_map[category# object] = set(event ids)
    category_event_map = defaultdict(set())
    for category_id in all_category_dict.keys():
        category = all_category_dict[category_id]
        event_ids = categoryid_event_map[category_id]
        if event_ids:
            category_event_map[category] = set(event_ids)

    #print "Time taken: ", time.time() - start
    return category_event_map


def get_event_score(user, event_ids, event_score):
    """
    Given a user and event_ids, returns a dictionary that maps the
    abstract events score for each event_id
    """
    if not event_score:
        event_score = defaultdict(lambda :0)
    #Mapping between event ids and all abstract categories.
    event_cat_dict = Category.objects.for_events(tuple(event_ids), 'A')
    ctree = CachedCategoryTree()
    event_abstract_score = random_tree_walk_algorithm(user, ctree.abstract_node,
                                                      ctree)
    #event_abstract_score is now a mapping of category objects to scores
    # Converting it to a mapping of category id to score
    event_abstract_score = dict([(cat.id, value) for cat,value in event_abstract_score.items()])
    # FIXME: This can be optimized.
    # Only calculate scores for events that you sample inside the
    # for category in categories loop.
    for event_id, abstract_category_ids in event_cat_dict.items():
        scores = [event_abstract_score[c] for c in abstract_category_ids]
        # FIXME: consider using a kernel function here instead of just max.
        event_score[event_id] = max(scores)
    return event_score

def filter_events(user, event_query_set, categories_dict,
                  number=settings.N, selected_events=set(),
                   event_score=None, events=None):
    """
    Input: User (required)            : person we are recommending to
           event_query (required)     : represents the input Events wuery set.
           categories_dict (required) : list of (concrete_categories, score)
           number (optional)          : Number of recommendations to provide
           selected_events (optional) : The set of events already selected events.
           event_score (optional)     : A dictionary representing event score.
    Output: List of events.
    Caution: Too many datastructures ahead!
    Description:
                 This function accepts as input a list of concrete_categories and
                 selects 'number' events for these concrete_categories
    #FIXME: Consider refactoring this function and testing individual bits.
                 - Performance consideration: adding a level(s) to the stack
                   will degrade performance.
                 - Trade-off is readability v/s performance :(
    #FIXME: You might not need to score all events. Only those selected during
            the sampling phase and the ones in its pool.

    Steps:
         - We start with generating
    """
    event_category = {}  # This is slightly confusing. The idea is that this
    if not events:
        events = generate_category_mapping(event_query_set, categories_dict)
        #used for ranking by categories
        event_category = dict([(e, categories_dict[k])
                               for k,v in events.items() for e in v])
    # events is now a dictionary of concrete category keys mapping to event ids.

    #Optimization to return early if we don't have enough events:
    if sum(map(len, events.values())) <= number:
        return [e for e in event_query_set]

    # Remove all concrete_categories that do not have any events.
    # This way, we only sample concrete_categories for which we have events.
    for key in set(categories_dict.keys()) - set(events.keys()):
        del categories_dict[key]
    concrete_categories = sample_category_distribution(categories_dict.items(),
                                                       number)

    # Remove already selected events
    for concrete_cat in concrete_categories:
        # Select only those events that have not yet been selected.
        events[concrete_cat] = events[concrete_cat] - selected_events

    # This can be optimized later.
    # event_score contains.
    # THIS IS A SERIOUS BOTTLENECK
    events_for_categories = [events[cat] for cat in set(concrete_categories)]
    events_for_categories = set([a for b in events_for_categories for a in b])
    event_score = defaultdict(lambda :0)
    events_for_categories = events_for_categories - selected_events \
                            - set(event_score.keys())
    event_score = get_event_score(user, events_for_categories, event_score)

    # This maintains a count of the number of missing events that need to be
    # sampled for again.

    missing_count = 0
    unique_categories = set(concrete_categories)
    for category in unique_categories:
        # Sample an event for each category based on the abstract score.
        count = concrete_categories.count(category)
        event_ids = sample_distribution([(event_id, event_score[event_id])
                                     for event_id in events[category]],
                                       count)

        for event_id in event_ids:
            selected_events.add(event_id)
            # This ensures an already selected event does not get selected again
            events[category].discard(event_id)
        missing_count += count - len(set(event_ids))

        if len(events[category]) == 0 :
            del events[category]

    if missing_count > 0 and len(events) > 0:
        # This is "hopefully" unlikely to happen if there are enough events in
        # each category. If we get to this point, it means we don't have enough
        # events for the concrete_categories sampled resample from the concrete_categories and
        # recommend more events. This is one place where we could break the
        # settings.max_probability cap. But this could be necessary for example
        # if you are in Waukeesha, Wisconsin and only have movies to go to.
        # Or worse, if you are in Wahkon, Wisconsin and have no events or
        # literally  nothing around you.

        more_events = set(filter_events(user, event_query_set,
                                        categories_dict, missing_count,
                                        selected_events,
                                        event_score,
                                        events))
        selected_events.union(more_events)
    # print "Number of events recommended: ", len(selected_events)
    #print fuzzy_sort(selected_events)

    # FIXME select related is an ugly fix, because it costs us 1 JOIN.
    # FIXME look into refactoring your category_dict to have category_id keys
    # FIXME then lookup using event.category_id which won't hit the db
    #returned_events = Event.objects.filter(id__in=selected_events)
    #this can be made more efficient with a single query. Leaving out for now.
    if event_category:
        event_score_list = [(event_category[ev], ev) for ev in selected_events]
        semi_sorted = semi_sort(event_score_list, min(3, len(selected_events)))
        return fuzzy_sort(semi_sorted)

    return [ev for ev in selected_events]

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
    if len(events) > 2:
        for index in range(len(events)-1):
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
def score_multiplier(parent, inkey, function_of_parent, outkey):
    """
    Stub
    """
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
        score = settings.scoringFunction(parent.score)
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
        return [1.0/len(lst) for e in lst]


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


def sample_category_distribution(distribution, trials=1, category_count=None):
    """
    Given a distribution of [(item,score)] samples items.
    Items are first normalized by scores and then sampled from it.
    NOTE: Rewrite this function. Factor out the sampling from any of the
    category tree or event sampling logic.
    """
    # Convert into a cumulative distribution
    cumulative_distribution = numpy.cumsum(normalize([x[1] for x in distribution]))
    # print "Distribution: ",  CDFDistribution
    return_list = []
    if not category_count:
        category_count = defaultdict(lambda : 0)
    for i in range(trials):
        value = random.random()

        count = bisect_left(cumulative_distribution, value)
        if distribution:
            if category_count[(distribution[count])[0]] < (
                trials * settings.max_probability
                ):
                return_list += [(distribution[count])[0]]
                category_count[(distribution[count])[0]] += 1
            else:
                if len(distribution) > 1:
                    del distribution[count]
                else:
                    category_count[(distribution[count])[0]] -=1
                return_list += sample_category_distribution(distribution,
                                                 trials-i,
                                                 category_count)
                break

    # import pdb; pdb.set_trace()
    return return_list

"""
# For later
# This might not be worth it. In terms of performance the one implemented
# is exactly the same.
# However, a factored out sample distribution makes more engineering sense.
# Reconsider design.

def sample_category_distribution_test(distribution, trials=1):
    return_list = sample_distribution(distribution, trials)
    category_count = defaultdict(lambda : 0)

    for category in return_list:
        category_count[category] += 1
    max_count = trials * settings.max_probability
    remainder = 0
    categories_to_remove = []
    for category, count in category_count.iteritems():
        if count > max_count:
            remainder += count - max_count
            category_count[category] = max_count
            categories_to_remove.append(category)

    if remainder > 0:
        # if there are sufficient elements, remove it from the sampling
        # and resample for remainder more elements.
        for category, score in distribution:

        sample_category_distribution_test(distribution, remainder)
"""

def sample_distribution(distribution, trials=1):
    """
    This is the factored out weighted sampling distribution.
    """
    if not distribution:
        return []
    cumulative_distribution = numpy.cumsum(normalize([x[1]
                                                      for x in distribution]))
    return_list = []
    for i in range(trials):
        # This generates a number between 0 and 1
        value = random.random()
        # Get value in in cumulative_distribution (a) such that
        # a(i) < value <= a(i+1)
        # This uses the more efficient binary search instead of the previous
        # linear scan.
        # Bisect works here because the cumulative_distribution list is
        # already 'sorted'.
        bncount = bisect_left(cumulative_distribution, value)
        return_list.append(distribution[bncount][0])
    return return_list
