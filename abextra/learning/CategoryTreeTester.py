from learning import CategoryTree
import unittest

#-------------------------
#Function level Tests:
#-------------------------

# General tests for correctness (see some of the tests implemented in mlTester.py

#Number of categories in the category tree is the same for every user
#Summation of Probabilistic walk scores for all categories should be 1.0
#Summation of Probabilistic walk scores for all mid-leafs should be 1.0
# If for any user, no information is available for a particular category, then the default_behavior should be assumed.

# Tests for the future
# Iterator tests to ensure every category is iterated over
# Iterator methods for Functions to be applied iteratively:
#       i) Top-Down recursion
#      ii) Bottom-up recursion

#-------------------------
# Algorithm level Tests
# These tests might need to be in a separate module
#-------------------------

# Performance for an algorithm can be determined on two factors
# a) Niche exploration
# b) Niche exploitation
#
# For our prototype, we are only considering Niche exploitation. For this purpose, we want to identify
# A> How many reloads (requests for recommendations) does it take before the entire recommendation is for a single category. This depends on one primary factor:
# >> The number of pieces of information we recieved between each request for recommendation
# B> Given a users preference for a category with a fairly high association coefficient, how long does it take to ensure that the sibling categories do not get recommended.
#!The functionality for the following tests are yet to be implemented
# C> Not recommending particular categories unless unlocked.Test: Ensure unlocked categories do not get recommended.
# D> Ensure the number of recommendations are proportional to the number of events to be recommended. 
