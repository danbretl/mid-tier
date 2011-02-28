"""
This file serves as a shortcut for test cases. While debugging machine learning
it is difficult to have to wait for the test framework to load all the 
databases, and we have to find a good solution to divide algorithm testing from
the rest of the tests (algorithm tests are difficult to debug). Once we're happy
with how these work I intend to make them into test cases.

While debugging, I usually thus used something like

echo 'from learning import simple_testing' | python manage.py shell
"""

from learning import testing_simulation
from django.contrib.auth.models import User
from learning import user_behavior

u = User.objects.get(id=1)

def runtests():
    """some really basic tests"""
    behavior_db = user_behavior.UserBehaviorDict()
    category_ids = map(testing_simulation.get_category_id, ['Bars','Clubs', 'Plays','Sculpture','Fallon','Wine','Sculpture'])
    #person = testing_simulation.DeterministicPerson(category_ids)
    person = testing_simulation.TransitionSimulatedPerson(db=behavior_db)
    print "running rounds"
    
    a = time.time()
    person.run_rounds(50, 100)
    print "Time to run rounds:", time.time() - a
    person.plot_gvix("plot_gvix.pdf")
    person.plot_preference_distribution("plot_preference_distribution.pdf")

runtests()

#cProfile.run('from testing_simulation import runtests; ', "simpletest")
#p = pstats.Stats("simpletest")
#p.strip_dirs().sort_stats("cumulative").print_stats(numprint)

#print [person.get_precision_recall(r) for r in person.rounds]

#c = testing_framework.EventureUser(u,categories=['Bars','Clubs','Musical','Poetry','Classic', 'Wine','Plays','Sculpture','Fallon'])
#c = TestingFramework.EventureUser(u,categories=['Museum','Daily Show'])
#c.calculate_plot_metrics(100)
#c.iterated_preferred_categories_plot(100,1)
"""

from events.models import Event, CategoryManager, Category
a = CategoryManager()
event_ids = [e.id for e in Event.objects.filter(id__lt=10)]
dictionary = a.for_events(event_ids,category_types='C')

print dictionary
"""
