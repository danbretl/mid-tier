from django.conf.urls.defaults import *

from piston.resource import Resource
from piston.authentication import HttpBasicAuthentication

from api.handlers import EventHandler

auth = HttpBasicAuthentication()
ad = { 'authentication': auth }

event_resource = Resource(handler=EventHandler, **ad)
# event_resource = Resource(handler=EventHandler)

urlpatterns = patterns('',
    url(r'^events/(?P<event_id>[^/]+)/$', event_resource),
)
