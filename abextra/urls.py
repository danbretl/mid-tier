from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin
from django.views.static import serve
from autocomplete.views import autocomplete

from api import urls as api_urls


admin.autodiscover()

urlpatterns = patterns('',
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    url(r'^admin/', include(admin.site.urls)),          # admin

    url(r'^api/', include(api_urls)),                   # piston api

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
from events.api import EventResource, EventSummaryResource, EventRecommendationResource
from behavior.api import EventActionResource
from events.api import CategoryResource

v1_api = Api(api_name='v1')

# User / Registration
v1_api.register(UserResource())

# Event / Recommendation
v1_api.register(EventResource())
v1_api.register(EventSummaryResource())
v1_api.register(EventRecommendationResource())

# Behavior / Reset
v1_api.register(EventActionResource())

# Category
v1_api.register(CategoryResource())

urlpatterns += patterns('',
    (r'^tapi/', include(v1_api.urls)),
)