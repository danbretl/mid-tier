
from learning import testing_framework
from django.contrib.auth.models import User

u = User.objects.get(id=1)
c = testing_framework.EventureUser(u,categories=['Bars','Clubs','Musical','Poetry','Classic', 'Wine','Plays','Sculpture','Fallon'])
#c = TestingFramework.EventureUser(u,categories=['Museum','Daily Show'])
#c.calculate_plot_metrics(100)
c.iterated_preferred_categories_plot(100,10)
"""

from events.models import Event, CategoryManager, Category
a = CategoryManager()
event_ids = [e.id for e in Event.objects.filter(id__lt=10)]
dictionary = a.for_events(event_ids,category_types='C')

print dictionary
"""
