import sys
from settings import *

if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME' : ':memory:',
        'TEST_NAME': ':memory:',
    }

