"""ML.py
Created by David Robinson
1/19/10

Some basic prototypes of machine learning algorithms for Abextra"""

### PARAMETERS ###
DEFAULT_ASSOC = 0

### IMPORTS ###
import sys
import os
import time
import math
import operator

### FUNCTIONS ###

def flatten_linear(x, lst):
    """given x, an association constant between 0 and 1,
    and lst, a list of probabilities adding up to 1, move
    them all towards the even vector linearly depending on x"""
    mid = 1.0 / len(lst)
    return [mid + (1-x)*(y-mid) for y in lst]

def sigmoid(x):
    """sigmoid function"""
    return 1 / float(1 + math.exp(-x))

def flatten_sigmoid(x, lst):
    """flatten using the sigmoid function"""
    # find the mean, sigmoid around that
    m = sum(lst) / float(len(lst))
    print [sigmoid(e - m) for e in lst]
    return normalize([sigmoid(e - m) + x for e in lst])

def ifelse(c, t, f):
    if c: return t
    return f

def decrease(x, d):
    """decrease d by a factor that is smaller
    and smaller the greater the difference is"""
    # limit
    if x == 0:
        return d
    return d * (1 - math.exp(-d/x))

def normalize(lst):
    """normalize all values so they add up to 1"""
    s = float(sum(lst))
    return [e / s for e in lst]

def flatten_matrix(x, lst):
	"""flatten by multipling by a matrix with diagonal 1's
	and the rest x's, then normalizing"""
	newlst = []
	for i in range(len(lst)):
		total = 0
		for j, e in enumerate(lst):
			if i == j:
				total += e
			else:
				total += e * x
		newlst.append(total)
	return normalize(newlst)

#print flatten_matrix(.1, [.01, .01, 100])
#sys.exit()

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

print flatten_expo(.1, [.01, .01, 100])
sys.exit()

def round_lst(lst):
    """round each item in a list for display"""
    return ["%.4f" % x for x in lst]

if False:
	print "F(K, L)"
	for K, L in [(1, [1, 2]), (1, [10, 20]), (1, [100, 200]),
				 (10, [1, 2]), (10, [10, 20]), (10, [100, 200]),
				 (.1, [1, 2]), (.1, [10, 20]), (.1, [100, 200]),
				 (.1, [.1, .2]), (0, [1, 2]),
				 (1, [1, 2, 3, 4]), (1, [1, 1000]),
				 (1, [0, 1]), (1, [0, 5]), (1, [0, 10]),
				 (10, [0, 1]), (10, [0, 5]), (10, [0, 10]),
				 (10, [1, 10]), (5, [10, 40, 50, 60])]:
		print "K = ", K, "L =", L, round_lst(flatten_expo(K, L))
	sys.exit()

### CLASSES ###

class SimpleTree:
    """this is an simple implementation of a category tree, but
    it is meant to follow a pattern. As long as whatever interface we
    end up using for a user's tree, however it relates to SQL
    tables or whatever, has the public methods that are below,
    this machine learning algorithms here will work with it"""
    def __init__(self, name, val, children=[], assoc=DEFAULT_ASSOC):
        """must be given a name, a value representing how
        much the user likes this, and optionally children"""
        self.name = name
        self.val = val
        self.children = children
        self.assoc = assoc
        
        # set up all total values
        self.update_totals()
    
    def get_val(self):
        """get the value that the tree is scored on"""
        return self.val
    
    def association_constant(self):
        """value from 0 to 1- 0 is not associative, 1 is perfectly
        associative"""
        return self.assoc
    
    def get_children(self):
        """return a list of child SimpleTree objects"""
        return self.children
    
    def total_value(self):
        """return the total value of all nodes under this tree"""
        return self.total
    
    def update_totals(self):
        """update and cache all total values- should be run once
        before any iteration is done. If any individual values
        are changed on the tree (for example, if we are doing
        a new recommendation round), this method must be
        re-run"""
        for t in self.children:
            t.update_totals()
        self.total = self.val + sum([t.total for t in self.children])
    
    def num_leaves(self):
        return 1 + sum([c.num_leaves() for c in self.children])
    
    def __repr__(self):
        """string representation in nested parentheses"""
        ret = "'" + self.name + "'" + "=" + str(self.val)
        if self.assoc != 0:
            ret += "[" + str(self.assoc) + "]"
        if len(self.children) > 0:
            ret += "(" + ",".join(map(str, self.children)) + ")"
        return ret

class EventSelector:
    """this is a toy example of a class that will, once it is integrated
    with SQL, serve two functions. First, it will tell us how many events
    fall under a specific category. Second, it will allow us to sample 
    k events from a given category"""
    def __init__(self, categories):
        """this is the toy part- given a list of tuples of
        names of categories and the number of events in them"""
        self.lst = []
        
        for category, n in categories:
            self.lst += [category for i in range(n)]
    
    def count(self, category):
        """given the name of a category, return how many events
        are in that category"""
        return self.lst.count(category)
    
    def random_sample(self, category, k):
        """given the name of a category, return a sample
        of k events from it"""
        # check that you are not sampling too many categories-
        # such a problem will have to be solved at a higher level
        if k > self.count(category):
            raise Exception("Asked for " + str(k) + " items of category k, " +
                            "when only " + str(self.count(category)) + " exist")
        
        # this does nothing but return a list of length k, with
        # event names of (for category A) [A_1, A_2, A_3...]
        return [category(i) + str(i) for i in range(k)]

class CategorySampler:
    def __init__(self, tr, func):
        """given a CategoryTree and a function to use for associative
        flattening"""
        self.tr = tr
        self.func = func
    
    def probability_distribution(self):
        """return a list of tuples of names and probabilities of being
        sampled"""
        return self.__probability_distribution_helper(self.tr, 1)
    
    def __probability_distribution_helper(self, t, prob):
        """given a tree and the probability of reaching this point,
        return the probabilities of each name within it"""
        dist = self.__distribution(t)
        
        ret = [(t.name, prob * dist[0])]
        
        for child, p in zip(t.get_children(), dist[1:]):
            ret += self.__probability_distribution_helper(child, prob * p)
        
        return ret
        
    def __distribution(self, t):
        """given a tree, return a distribution of the probabilities
        of choosing first the node itself and then each of the node's
        children in order"""
        # what are the trees we could progress along and their values
        values = [t.get_val()] + [c.total_value() for c in t.get_children()]
        # normalize and then flatten out these values
        return self.func(t.association_constant(), normalize(values))
    
def timing_test():
    """simple test where a tree with a large number of roots is created and the
    probability distribution calculated many times in order to find the 
    time of the algorithm"""
    tr = SimpleTree("A", 1, [SimpleTree("B", 1), 
            SimpleTree("C", 1, [SimpleTree("D", 6), SimpleTree("E", 1)], assoc=.5)])
    tr = SimpleTree("F", 1, [tr, tr, tr, tr])
    tr = SimpleTree("G", 1, [tr, tr, tr, tr, tr, tr])
    s = CategorySampler(tr, flatten_linear)
    
    NUM_TRIALS = 1000
    time_a = time.time()
    for i in range(NUM_TRIALS):
        s.probability_distribution()
    print ("Calculation of distribution of tree with " + str(tr.num_leaves()) + 
            " leaves takes " + str(total_time / NUM_TRIALS) + " seconds")

if __name__ == "__main__":
    # TEST SUITE
    tr = SimpleTree("A", 1, [SimpleTree("B", 1), 
            SimpleTree("C", 1, [SimpleTree("D", 10000), SimpleTree("E", 1)], assoc=-1)])
    s = CategorySampler(tr, flatten_expo)
    print tr
    print s.probability_distribution()
    
    #print flatten_sigmoid(1, [2, 102])
