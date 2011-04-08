from django.conf.urls.defaults import *

from piston.resource import Resource
from piston.authentication import HttpBasicAuthentication, OAuthAuthentication

from api.handlers import EventHandler, EventActionHandler, CategoryHandler
from api.handlers import EventDetailHandler, EventListHandler



from emitters import Emitter, JSONEmitterMinified  # FIXME hack to register the emitter
Emitter.register('json', JSONEmitterMinified, 'application/json; charset=utf-8')

auth = HttpBasicAuthentication()
ad = { 'authentication': auth }

events = Resource(handler=EventHandler, **ad)
event_actions = Resource(handler=EventActionHandler, **ad)
categories = Resource(handler=CategoryHandler, **ad)
event_list = Resource(handler=EventListHandler, **ad)
event_detail = Resource(handler=EventDetailHandler, **ad)

# event_resource = Resource(handler=EventHandler, authentication=OAuthAuthentication())

# urlpatterns = patterns('piston.authentication',
#     url(r'^oauth/request_token/$','oauth_request_token'),
#     url(r'^oauth/authorize/$','oauth_user_auth'),
#     url(r'^oauth/access_token/$','oauth_access_token'),
# )

urlpatterns = patterns('',
    # url(r'^events/$', events),
    url(r'^events/$', events),
    url(r'^event_detail/(?P<event_id>\d+)/$', event_detail),
    url(r'^event_list/$', event_list),
    url(r'^search/(?P<search_terms>.*?)/$', event_list),
    url(r'^categories/$', categories),

    # url(r'^actions/$', event_actions),
    # url(r'^actions(/(?P<event_id>[^/]+))?/$', event_actions),
    url(r'^actions/$', 'behavior.views.create_eventaction'),    # TODO temp hack to go around weirdness with piston's POST
    url(r'^actions/reset/$', 'behavior.views.reset_behavior'),  # TODO temp hack - use piston
    url(r'^actions/reset_all/$', 'behavior.views.reset_behavior_all'),  # TODO temp hack - use piston
)
