from django.conf.urls.defaults import *

from piston.resource import Resource
from piston.authentication import HttpBasicAuthentication, OAuthAuthentication

from api.handlers import EventHandler, EventActionHandler, CategoryHandler

auth = HttpBasicAuthentication()
ad = { 'authentication': auth }

events = Resource(handler=EventHandler, **ad)
event_actions = Resource(handler=EventActionHandler, **ad)
categories = Resource(handler=CategoryHandler, **ad)

# event_resource = Resource(handler=EventHandler, authentication=OAuthAuthentication())

# urlpatterns = patterns('piston.authentication',
#     url(r'^oauth/request_token/$','oauth_request_token'),
#     url(r'^oauth/authorize/$','oauth_user_auth'),
#     url(r'^oauth/access_token/$','oauth_access_token'),
# )

urlpatterns = patterns('',
    # url(r'^events/$', events),
    url(r'^events(/(?P<event_id>[^/]+))?/$', events),
    url(r'^categories(/(?P<parent_node_title>[^/]+))?/$', categories),

    # url(r'^actions/$', event_actions),
    # url(r'^actions(/(?P<event_id>[^/]+))?/$', event_actions),
    url(r'^actions/$', 'behavior.views.create_eventaction'),    # TODO temp hack to go around weirdness with piston's POST
    url(r'^actions/reset/$', 'behavior.views.reset_behavior'),  # TODO temp hack - use piston
)
