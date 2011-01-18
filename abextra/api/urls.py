from django.conf.urls.defaults import *

from piston.resource import Resource
from piston.authentication import HttpBasicAuthentication, OAuthAuthentication

from api.handlers import EventHandler

auth = HttpBasicAuthentication()
ad = { 'authentication': auth }

event_resource = Resource(handler=EventHandler)
# event_resource = Resource(handler=EventHandler, **ad)
# event_resource = Resource(handler=EventHandler, authentication=OAuthAuthentication())
# event_resource = Resource(handler=EventHandler, **ad)
# event_resource = Resource(handler=EventHandler)

urlpatterns = patterns('piston.authentication',
    url(r'^oauth/request_token/$','oauth_request_token'),
    url(r'^oauth/authorize/$','oauth_user_auth'),
    url(r'^oauth/access_token/$','oauth_access_token'),
)

urlpatterns += patterns('',
    url(r'^events/((?P<event_id>[^/]+)/)?$', event_resource),
)
