from django.core.management.base import NoArgsCommand, CommandError
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group

class Command(NoArgsCommand):
    help = 'Create a bunch of machine learning users.'

    def handle(self, **options):
        try:
            group = Group.objects.get(name='testers_ml')
            data = dict(password1='abexml', password2='abexml')
            for i in range(100):
                data.update(username='tester_ml_%i' % i)
                f = UserCreationForm(data=data)
                if f.is_valid(): u = f.save()
                group.user_set.add(u)
        except Exception, e:
            raise CommandError(e)
        self.stdout.write('Successfully created tester_ml users')