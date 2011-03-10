from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin
from django.views.static import serve
from autocomplete.views import autocomplete

from api import urls as api_urls


admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^abextra/', include('abextra.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    url(r'^admin/', include(admin.site.urls)),          # admin

    url(r'^api/', include(api_urls)),                   # piston api

    url('^autocomplete/', include(autocomplete.urls)),  # autocomplete

    url(r'^static/(?P<path>.*)$', serve, {              # statics
        'document_root': settings.STATIC_DOC_ROOT
    }),
)
