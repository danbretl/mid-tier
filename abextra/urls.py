from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin
from django.views.generic.simple import direct_to_template

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
    url(r'^alpha/$', direct_to_template,
        {'template': 'alphasignup/index.html'},
        name='alpha_home'
    ),
    url(r'^alpha/accounts/', include('alphasignup.urls')),
    url(r'^alpha/about/$', direct_to_template,
        {'template': 'alphasignup/about.html'},
        name='alpha_about_us'
    ),

    # ===========
    # = Landing =
    # ===========
    url(r'^$', direct_to_template,
        {'template': 'index.html'},
        name='landing'
    ),

    # ================
    # = Autocomplete =
    # ================
    url(r'^autocomplete/', include(autocomplete.urls)),
)

# ===========
# = Statics =
# ===========
from django.views.static import serve
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns += staticfiles_urlpatterns()
urlpatterns += (
    url(r'^site\_media\/media\/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    url(r'^favicon\.ico$', 'django.views.generic.simple.redirect_to',
        {'url': settings.STATIC_URL + 'images/favicon.ico'}
    ),
)
