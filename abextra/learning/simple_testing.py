"""
from learning import TestingFramework
from django.contrib.auth.models import User

u = User.objects.get(id=1)
c = TestingFramework.EventureUser(u,categories=['Bars','Clubs','Musical','Poetry'])
#c = TestingFramework.EventureUser(u,categories=['Museum','Daily Show'])
c.calculate_plot_metrics(50)
"""


from events.models import Event, CategoryManager, Category
a = CategoryManager()
e = Event.objects.filter(id__lt=10)
dictionary = a.for_events(e)
