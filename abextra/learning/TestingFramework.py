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
    
    def __init__(self, user=None, categories=None):
        """
        Initialize a new user and prepare to get recommendations from scratch.
        """
        self.accuracy_dictionary = {}
        if user:
            self.user = user
            self.delete_user = False
        else:
            # Create and assign a new user.
            # if necessary later delete the user as well. But this might not be necessary since in Django we will be working
            # with a fresh database that will in any case be destructed at the end of testing.
            self.delete_user = True
            success = False
            count = 0
            while not success:
                count += 1
                try:
                    self.user = User(username="test"+str(count), password='test'+str(count))
                    self.user.save()
                    success = True
                except:
                    success = False
        """
        for c in Category.objects.all():
            try:
                #See if event action aggregate exists.If it does, reset it to default.
                eaa = EventActionAggregate.objects.get(user=self.user,category=c)
            except:
                #Else create one.
                eaa = EventActionAggregate(user=self.user, category=c)
                
            default_eaa = EventActionAggregate.objects.get(user=settings.get_default_user(),category=c)
            eaa.g = default_eaa.g
            eaa.v = default_eaa.v
            eaa.i = default_eaa.i
            eaa.x = default_eaa.x
            eaa.save()
        """
        

        
        if categories:
            self.preferred_categories = set(categories)
        else:
            self.preferred_categories = set(self.get_random_categories())
            

    def __del__(self):
        if self.delete_user:
            self.user.delete()

        
    def get_random_categories(self,num_categories=None):
        if num_categories:
            x = num_categories
        else:
            x = random.randrange(1,8)
        return Category.objects.all().order_by('?')[:x]



    #ToDo: Make this generic so user behavior can be easily defined by an ML tester.
    def update_behavior(self,event_ids):
        """
        This is just one way of updating user behavior between recommendations.
        """
        if event_ids:
            events = [Event.objects.get(id=e) for e in event_ids]
            recommended_categories = self.get_recommended_categories(event_ids)
            #recommended_categories = [a for b in recommended_categories for a in b]
            #print recommended_categories
            result = [set(c).intersection(self.preferred_categories) for c in recommended_categories]

            for e,categories,recs in zip(events,result,recommended_categories):
                if categories:
                    for c in categories:
                        self.update_user_category_behavior(c,(1,0,0,0))
                else:
                    if recs:
                        #This was a bad recommendation X it.
                        #if random.random() < 0.15 :                            # Roughly 15% of the time we delete a category.
                        for c in recs: 
                            self.update_user_category_behavior(c,(0,0,0,1))



    def update_user_category_behavior(self,category,(g,v,i,x)=(0,0,0,0)):
        eaa = EventActionAggregate.objects.get(user=self.user, category=category)
        eaa.g += g
        eaa.v += v
        eaa.i += i
        eaa.x += x
        eaa.save()


    def reset_user_behavior(self, category):
        try:
            eaa = EventActionAggregate.objects.get(user=settings.get_default_user(), category = category)
            g = eaa.g
            v = eaa.v
            i = eaa.i
            x = eaa.x
        except:
            g, v, i, x = 0, 0, 0, 0

        eaa = EventActionAggregate.objects.get(user=self.user, category=category)
        eaa.g = g
        eaa.v = v
        eaa.i = i
        eaa.x = x
        eaa.save()

    def return_user_behavior(self):
        try:
            for c in Category.objects.all():
                eaa = EventActionAggregate.objects.get(user=self.user, category=c)
                return (eaa.g,eaa.v,eaa.i,eaa.x)
        except:
            return (None,None,None,None)


    def get_recommended_categories(self,event_ids=None):
        if event_ids:
            events = Event.objects.in_bulk(event_ids)
            recommended_categories = [[e.concrete_category]  for e in events]
            abstract_categories = [e.categories.get_query_set() for e in events]
            #print "abstract_categories: ", abstract_categories
            #print "recommended_categories: ", recommended_categories
            #import ipdb; ipdb.set_trace()
            recommended_categories = [ i + j for i,j in izip(recommended_categories,abstract_categories)]
            return recommended_categories
        else:
            return [[]]

        
    def calculate_recall_value(self, event_ids):
        if event_ids:
            recommended_categories = set([a for b in self.get_recommended_categories(event_ids) for a in b])
            #print "recommended_categories: ", recommended_categories
            #print "user preferred_categories: ", self.preferred_categories
            correct_recommendations = recommended_categories.intersection(self.preferred_categories)
            return len(correct_recommendations) * 100.0 / len(self.preferred_categories)
        else:
            return 0.0


    def calculate_precision_value(self, event_ids=None):
        if event_ids:
            recommended_categories = self.get_recommended_categories(event_ids)
            result = [len(set(c).intersection(self.preferred_categories))>0 for c in recommended_categories]
            #print "precision result: ", result
            return sum(result) * 100.0 / len(result)
        else:
            return 0.0


    def plot(self,lst_lst, description="", color="blue", xlabel="x-axis", ylabel="y-axis", save_file="test.pdf"):
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
        events = ml.recommend_events(self.user)
        for i in range(N):
            print "In loop: ", i
            self.update_behavior(events)
            #print "Events: ", events
            event_ids = ml.recommend_events(self.user)
            precision.append(self.calculate_precision_value(event_ids))
            recall.append(self.calculate_recall_value(event_ids))
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


    def get_accuracy(self):
        return accuracy_dictionary

