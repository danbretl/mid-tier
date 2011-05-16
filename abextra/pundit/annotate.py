"""
Author: Vikas Menon
Date: Mar 29 2011

Current (Basic) Functionality:
This module currently only uses NLTK.

Semi-Advanced:
In the future Pundit will be an ensemble classifier that could be driven with
meta level information (information about locations, times, web searches etc).

Advanced Functionality:
Currently annotations (categories) are assumed to be strings.
Later Pundit could be designed to build complete annotated objects as output.
Example: Annotating both Abstract and Concrete in the same run.

"""
from nltk import NaiveBayesClassifier, classify
from numpy import std
import random

class Pundit(object):
    """
    Current Basic natual language based classifier
    """
    def __init__(self, training_set, expert_function=None):
        """

        Argumens:
        - 'self' -
        - 'training_set': This is a list of the form [(features, category)]
                          features is a dictionary of the form
                          {feature_name:feature_value}
        - 'expert_function': This is the expert annotation function that
                             given an object returns its category
                             This function should return None if unable to
                             classify.
        """
        self.training_set = training_set
        self.labels = set([x[1] for x in training_set])
        self.expert_function = expert_function
        self.classifier = NaiveBayesClassifier.train(training_set)

    def cross_validation(self):
        """
        This is 10 fold cross validation.
        """
        total_set = random.shuffle(self.training_set)
        len_fold = len(total_set)/10
        folds = [ total_set[ count * len_fold : len_fold * (count + 1)]
                  for count in range(10)]
        list_accuracy = []
        for test_set in folds:
            train_set = list(set(total_set) - set(test_set))
            classifier = NaiveBayesClassifier.train(train_set)
            accuracy = classify.accuracy(classifier, test_set)
            print 'Accuracy: ', accuracy
            list_accuracy.append(accuracy)
        print 'Mean = ', sum(list_accuracy)/len(list_accuracy)
        print 'SD   = ', std(list_accuracy)

    def classify(self, event):
        """
        Main classifier method.
        """
        if self.expert_function:
            category = self.expert_function(event)
            if category:
                return category

        features = {'title':event.title, 'description': event.description}
        return self.classifier.classify(features)
