from django.conf.urls.defaults import *
from tastypie.api import Api

from accounts.resources import UserResource
from behavior.resources import EventActionResource
from events.resources import CategoryResource
from events.resources import EventResource, EventFullResource, FeaturedEventResource
from events.resources import OccurrenceResource, OccurrenceFullResource
from events.resources import EventSummaryResource, EventRecommendationResource
from places.resources import PlaceResource, PointResource, CityResource
from places.resources import PlaceFullResource, PointFullResource
from prices.resources import PriceResource

# ===========================
# = Instantiate Api Version =
# ===========================
api_v1 = Api(api_name='v1')

# =======================
# = User / Registration =
# =======================
api_v1.register(UserResource())

# ==========================
# = Event / Recommendation =
# ==========================
api_v1.register(EventResource(), canonical=True)
api_v1.register(EventFullResource())
api_v1.register(FeaturedEventResource())
api_v1.register(OccurrenceResource(), canonical=True)
api_v1.register(OccurrenceFullResource())
api_v1.register(EventSummaryResource(), canonical=True)
api_v1.register(EventRecommendationResource())

# ==========
# = Places =
# ==========
api_v1.register(PlaceResource(), canonical=True)
api_v1.register(PlaceFullResource())
api_v1.register(PointResource(), canonical=True)
api_v1.register(PointFullResource())
api_v1.register(CityResource(), canonical=True)

# ==========
# = Prices =
# ==========
api_v1.register(PriceResource(), canonical=True)

# ====================
# = Behavior / Reset =
# ====================
api_v1.register(EventActionResource(), canonical=True)

# ============
# = Category =
# ============
api_v1.register(CategoryResource(), canonical=True)

# ================
# = URL Patterns =
# ================
urlpatterns = patterns('',
    url(r'^', include(api_v1.urls)),
)
