from django.conf import settings
from dateutil.relativedelta import relativedelta
import os

# ============
# = Eventful =
# ============

API_KEY = settings.EVENTFUL_API_KEY
IMPORT_DIR = 'eventful'
IMPORT_IMAGE_DIR = os.path.join(settings.IMPORT_ROOT_DIR, IMPORT_DIR, settings.IMPORT_IMAGE_DIR_DEFAULT)
IMPORT_EVENT_HORIZON = relativedelta(months=1)
IMPORT_PARAMETERS = {
    'page_size': 50,
    'location': 'NYC',
#    'sort_order': 'popularity',
    'query': ''
}

