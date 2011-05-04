from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin
from django.views.static import serve

from autocomplete.views import autocomplete

admin.autodiscover()

urlpatterns = patterns('',
    # ====================================
    # = Admin / AdminDocs / LiveSettings =
    # ====================================
    url(r'^admin/', include(admin.site.urls)),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^settings/', include('livesettings.urls')),

    # ===============
    # = RESTful API =
    # ===============
    url(r'^api/', include('api.urls')),

    # ============================
    # = User Accounts via Userna =
    # ============================
    (r'^alpha/', include('alphasignup.urls')),

    # ================
    # = Autocomplete =
    # ================
    url('^autocomplete/', include(autocomplete.urls)),

    # ===========
    # = Statics =
    # ===========
    url(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_DOC_ROOT}),
    url(r'^favicon\.ico$', 'django.views.generic.simple.redirect_to',
        {'url': '/static/images/favicon.ico'}
    ),
)
