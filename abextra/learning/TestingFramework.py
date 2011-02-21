"""
This file is to ease generation of tests and will be used primarily for testing.
This functionality is intended for use currently only within the Django Testing framework.
Author: Vikas Menon
Date Created: 2/15/2011
"""

from matplotlib import pyplot as plt
from learning import ml, settings, CategoryTree
from behavior.models import EventActionAggregate
from django.contrib.auth.models import User
from events.models import Category, Event

from itertools import izip

import random

class EventureUser:
    """
    This class creates a new user for ML testing every time.
    """
    
    def __init__(self, user=None, categories=None, num_categories=None):
        """
        Initialize a new user and prepare to get recommendations from scratch.
        If given categories, use those as preferred, otherwise if given number of
        categories, create this many random ones
        """
        if user:
            self.user = user
            self.delete_user = False
        else:
            # Create and assign a new user.
            # if necessary later delete the user as well. But this might not be 
            # necessary since in Django we will be working with a fresh database 
            # that will in any case be destructed at the end of testing.
            self.delete_user = True
            success = False
            count = 0
            while not success:
                count += 1
                try:
                    self.user = User(username="test"+str(count), 
                                     password='test'+str(count))
                    self.user.save()
                    success = True
                except:
                    success = False
                    
        for c in Category.objects.all():
            try:
                #See if event action aggregate exists.If it does, reset it to default.
                eaa = EventActionAggregate.objects.get(user=self.user,category=c)
            except:
                #Else create one.
                eaa = EventActionAggregate(user=self.user, category=c)
            
            eaa.g, eaa.v, eaa.i, eaa.x = 0, 0, 0, 0
            eaa.save()
        
        if categories:
            self.preferred_categories = set([c.id for c in categories])
            self.preferred_categories = set([c.id for c in 
                                             self.get_random_categories(num_categories)])
    
    def __del__(self):
        if self.delete_user:
            self.user.delete()
        self.reset_user_behavior()

    def get_random_categories(self,num_categories=None):
        """
        get n random categories, or, if no number is given, a random number
        between 1 and 8
        """
        x = num_categories if num_categories else random.randrange(1,8)
        return Category.objects.all().order_by('?')[:x]

    #TODO: Make this generic so user behavior can be easily defined by an ML tester.
    def update_behavior(self,event_ids,category_ids):
        """
        This is just one way of updating user behavior between recommendations.
        """
        #import pdb; pdb.set_trace()
        #events = Event.objects.in_bulk(event_ids)
        #recommended_categories = [a for b in recommended_categories for a in b]            
        for categories, all_recs in category_ids:
            # if there is an intersection with preferred categories
            if self.preferred_categories.intersection(set(categories)):
                for c in categories:
                    self.update_user_category_behavior(c,(1,0,0,0))
            else:
                #This was a bad recommendation, so X it.
                #if random.random() < 0.15 :                            
                # Roughly 15% of the time we delete a category.
                for c in all_recs: 
                    self.update_user_category_behavior(c,(0,0,0,1))

    def update_user_category_behavior(self,category_id,(g,v,i,x)=(0,0,0,0)):
        """change the user's aggregate action by given (g,v,i,x) tuple"""
        eaa = EventActionAggregate.objects.get(user=self.user, 
                                               category_id=category_id)
        eaa.g += g
        eaa.v += v
        eaa.i += i
        eaa.x += x
        eaa.save()
        #except:
        #    pass

    def reset_user_behavior(self):
        """clear a user's behavior"""
        for category in Category.objects.all():
            eaa = EventActionAggregate.objects.get(user=self.user, category=category)
            eaa.g, eaa.v, eaa.i, eaa.x = 0, 0, 0, 0
            eaa.save()
            #except:
                # TODO: what exception is this meant to cover?
            #    pass

    def calculate_recall_value(self, event_ids,event_category_ids):
        """
        Return the recall between the recommended events given and this user's 
        preferred events. The recall is the % of types of events that the user 
        likes that appear in the recommendations
        """
        if event_ids:
            recommended_categories = set([a for b in event_category_ids for a in b])
            #print "recommended_categories: ", recommended_categories
            #print "user preferred_categories: ", self.preferred_categories
            correct_recommendations = recommended_categories.intersection(self.preferred_categories)
            return len(correct_recommendations) * 100.0 / len(pref_categories)
        else:
            return 0.0

    def calculate_precision_value(self, event_ids, 
                                        event_category_ids):
        """
        Return the precision between the recommended events given and the
        user's preferred categories. The precision is the % of recommendations
        that the user likes."""
        if event_ids:
            recommended_categories = event_category_ids
            result = [len(set(c).intersection(self.preferred_categories))>0 
                        for c in recommended_categories]
            #print "precision result: ", result
            return sum(result) * 100.0 / len(result)
        else:
            return 0.0


    def plot(self,lst_lst, description="", color="blue", xlabel="x-axis", 
                            ylabel="y-axis", save_file="test.pdf"):
        """helper function for plotting a list of lists of values"""
        for pos,lst in enumerate(lst_lst):
            plt.plot(lst,color)
        plt.title(description)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.savefig(save_file)
        plt.cla()

    
    def calculate_plot_metrics(self,N=1):
        """
        This method calculates and plots (currently precision and recall) metrics.
        """
        precision = []
        recall = []
        color = "blue"
        for i in range(N):
            print "In loop: ", i
            event_ids = ml.recommend_events(self.user)
            event_category_ids = ml.get_categories(event_ids)
            precision.append(self.calculate_precision_value(event_ids, event_category_ids))
            recall.append(self.calculate_recall_value(event_ids, event_category_ids))
            self.update_behavior(event_ids,event_category_ids)
            #print "Events: ", events
            #print "precision: ", precision
            #print "recall: ", recall

        print "precision: ", precision
        print "recall: ", recall
        plt.plot(precision,color=color)
        plt.title("Rate of learning for 1 category")
        plt.xlabel("Trials")
        plt.ylabel("Average presence in Recommendations")
        plt.savefig("learning/test_results/precision.pdf")
        plt.cla() 

        plt.plot(recall,color=color)
        plt.title("Recall")
        plt.xlabel("Trials")
        plt.ylabel("% of User preferred categories")
        plt.savefig("learning/test_results/recall.pdf")
        plt.cla() 


