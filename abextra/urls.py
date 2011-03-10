from django.conf.urls.defaults import *
from django.contrib import admin
from django.conf import settings

from autocomplete.views import autocomplete

admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^abextra/', include('abextra.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    url(r'^admin/', include(admin.site.urls)),          # admin

    url(r'^api/', include('abextra.api.urls')),         # piston api

    url('^autocomplete/', include(autocomplete.urls)),  # autocomplete

)

if settings.DEBUG:
    urlpatterns += (
        url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.STATIC_DOC_ROOT
        }),
    )
