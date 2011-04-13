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

import nltk


class Pundit(object):
    """
    
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

    def cross_validation(self):
        """
        This is 10 fold cross validation. 
        Arguments:
        - `self`:
        """
        total_set = random.shuffle(self.train_set)
        len_fold = len(total_set)/10
        folds = [ total_set[ count * len_fold : len_fold * (count + 1)]
                  for count in range(10)]
        list_accuracy = []
        for test_set in folds:
            train_set = list(set(total_set) - set(test_set))
            classifier = nltk.NaiveBayesClassifier.train(train_set)
            accuracy = nltk.classify.accuracy(classifier, test_set)
            print 'Accuracy: ', accurracy
            list_accuracy.append(accuracy)

        print "XXXXXXXXXXXXXXXXXXX"
        print 'Mean = ', sum(list_accuracy)/len(list_accuracy)
        
        print 'SD   = ', mean
        
        

        
    def natural_language(self):
        """
        
        Arguments:
        - `self`:
        """
        pass

    def classifier(self, event):
        """
        
        Arguments:
        - `self`:
        """
        if self.expert_function:
            category = self.expert_function(event)
            if category:
                return category

        features = {'title':event.title, 'description': event.description}
        return self.classifier.classify(features)
        
        
        

        
        

        

    
