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

    url('^autocomplete/', include(autocomplete.urls)),  # autocomplete

    url(r'^static/(?P<path>.*)$', serve, {              # statics
        'document_root': settings.STATIC_DOC_ROOT
    }),
    url(r'^favicon\.ico$',                              # favicon
        'django.views.generic.simple.redirect_to',
        {'url': '/static/images/favicon.ico'}
    ),

    url(r'^api/', include('newapi.urls')),              # APIs
)
