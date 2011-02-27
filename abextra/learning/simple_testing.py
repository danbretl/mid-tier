from learning import testing_simulation
from django.contrib.auth.models import User
from learning import user_behavior

u = User.objects.get(id=1)

"""some really basic tests"""
behavior_db = user_behavior.UserBehaviorDict()
category_ids = map(testing_simulation.get_category_id, ['Bars','Clubs', 'Plays','Sculpture','Fallon','Wine','Sculpture'])
person = testing_simulation.DeterministicPerson(category_ids, db=behavior_db)
print "running rounds"
person.run_rounds(200)
person.plot_gvix("plot_gvix.pdf")
person.plot_precision_recall("plot_precision_recall.pdf")
print [person.get_precision_recall(r) for r in person.rounds]

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
