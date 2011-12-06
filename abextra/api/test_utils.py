import datetime
from dateutil.relativedelta import relativedelta
from events.models import Category
from api.urls import api_v1
from django.utils import simplejson as json

API_BASE_URL = '/api'

class BaseFilterOptions(object):
    _PARAM_NAMES = None

    def _option(self, key):
        raise NotImplementedError

    def _param(self, key):
        option = self._option(key)
        option = option if isinstance(option, (tuple, list)) else (option,)
        return dict(zip(self._PARAM_NAMES, option))


class SimpleFilterOptions(BaseFilterOptions):

    def __init__(self):
        self.options_by_key = {}

    def _option(self, key):
        return self.options_by_key[key]


class CategoryFilterOptions(BaseFilterOptions):
    _PARAM_NAMES = ('concrete_parent_category',)

    def __init__(self):
        self.resource = api_v1._registry['category']
        categories = Category.objects.filter(slug__in=(
            'music', 'gatherings', 'nightlife', 'movies-media', 'sports-recreation',
            'hobbies-interest', 'arts-theater', 'food-drink'
        ))
        self.category_by_slug = dict((c.slug, c) for c in categories)

    def _option(self, slug):
        category = self.category_by_slug[slug]
        return self.resource.get_resource_uri(category)

    @property
    def music(self): return self._param('music')


class DateFilterOptions(SimpleFilterOptions):
    _PARAM_NAMES = ('dtstart_earliest', 'dtstart_latest')

    def __init__(self):
        super(DateFilterOptions, self).__init__()
        now = datetime.datetime.now()
        self.options_by_key.update({
            'today': (now.date(), now.date()),
            'this_weekend': (
                (now + relativedelta(weekday=5)).date(),
                (now + relativedelta(weekday=6)).date()
            ),
            'next_seven_days': (now.date(), (now +
                relativedelta(days=7)).date()
            ),
            'next_thirty_days': (now.date(), (now +
                relativedelta(days=30)).date()
            )
        })

    @property
    def today(self): return self._param('today')

    @property
    def this_weekend(self): return self._param('this_weekend')

    @property
    def next_seven_days(self): return self._param('next_seven_days')

    @property
    def next_thirty_days(self): return self._param('next_thirty_days')


class PriceFilterOptions(SimpleFilterOptions):
    _PARAM_NAMES = ('price_max',)

    def __init__(self):
        super(PriceFilterOptions, self).__init__()
        self.options_by_key.update({'free': 0,
                'under_twenty': 20,
                'under_fifty': 50})

    @property
    def free(self): return self._param('free')

    @property
    def under_twenty(self): return self._param('under_twenty')

    @property
    def under_fifty(self): return self._param('under_fifty')


class TimeFilterOptions(SimpleFilterOptions):
    _PARAM_NAMES = ('tstart_earliest', 'tstart_latest')

    def __init__(self):
        super(TimeFilterOptions, self).__init__()
        self.options_by_key.update({'morning': ('0900', '1159'),
                'afternoon': ('1200', '1759'), 
                'evening': ('1800', '2059'),
            # should be until 3am
                'late_night': ('2100','2359')})

    @property
    def morning(self): return self._param('morning')

    @property
    def afternoon(self): return self._param('afternoon')

    @property
    def evening(self): return self._param('evening')


def build_uri(endpoint):
    return '/'.join((API_BASE_URL, api_v1.api_name, endpoint, ''))

def try_json_loads(serialized):
    try:
        deserialized = json.loads(serialized)
        return deserialized
    except ValueError:
        pass

