from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin
from django.views.static import serve
from autocomplete.views import autocomplete

admin.autodiscover()

urlpatterns = patterns('',
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    url(r'^admin/', include(admin.site.urls)),          # admin
    url(r'^settings/', include('livesettings.urls')),   # live settings

    url(r'^api/', include('api.urls')),                   # piston api

    url('^autocomplete/', include(autocomplete.urls)),  # autocomplete

    url(r'^static/(?P<path>.*)$', serve, {              # statics
        'document_root': settings.STATIC_DOC_ROOT
    }),
)

# ================
# = TastyPie API =
# ================
from tastypie.api import Api

from events.api import UserResource
from events.api import CategoryResource
from events.api import EventResource, EventFullResource, FeaturedEventResource
from events.api import OccurrenceResource, OccurrenceFullResource
from events.api import EventSummaryResource, EventRecommendationResource
from behavior.api import EventActionResource
from places.api import PlaceResource, PointResource, CityResource
from places.api import PlaceFullResource, PointFullResource

v1_api = Api(api_name='v1')

# User / Registration
v1_api.register(UserResource())

# Event / Recommendation
v1_api.register(EventResource(), canonical=True)
v1_api.register(EventFullResource())
v1_api.register(FeaturedEventResource())
v1_api.register(OccurrenceResource(), canonical=True)
v1_api.register(OccurrenceFullResource())
v1_api.register(EventSummaryResource(), canonical=True)
v1_api.register(EventRecommendationResource())

# Places
v1_api.register(PlaceResource(), canonical=True)
v1_api.register(PlaceFullResource())
v1_api.register(PointResource(), canonical=True)
v1_api.register(PointFullResource())
v1_api.register(CityResource(), canonical=True)


# Behavior / Reset
v1_api.register(EventActionResource(), canonical=True)

# Category
v1_api.register(CategoryResource(), canonical=True)

urlpatterns += patterns('',
    (r'^tapi/', include(v1_api.urls)),
)
