from learning import TestingFramework
from django.contrib.auth.models import User

u = User.objects.get(id=1)
c = TestingFramework.EventureUser(u)
c.calculate_plot_metrics(10)

