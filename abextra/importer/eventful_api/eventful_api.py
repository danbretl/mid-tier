"""
    Yeah... Kinda stolen... Not very precious code to begin with...
    I added http pooling for work with eventlet concurrency. booya
"""

import eventlet
from eventlet import pools
from eventlet.green import urllib, urllib2

httplib2 = eventlet.import_patched('httplib2')
import md5
import simplejson

class APIError(Exception):
    pass

class API:
    def __init__(self, app_key, server='api.eventful.com'):
        self.app_key = app_key
        self.server = server
        self.httpool = pools.Pool()
        self.httpool.create = httplib2.Http

    def call(self, method, **args):
        "Call the Eventful API's METHOD with ARGS."
        # Build up the request
        args['app_key'] = self.app_key
        if hasattr(self, 'user_key'):
            args['user'] = self.user
            args['user_key'] = self.user_key
        args = urllib.urlencode(args)
        url = "http://%s/json/%s?%s" % (self.server, method, args)

        # Make the request
        with self.httpool.item() as http:
            response, content = http.request(url, "GET")

        # Handle the response
        status = int(response['status'])
        if status == 200:
            try:
                return simplejson.loads(content)
            except ValueError:
                raise APIError("Unable to parse API response!")
        elif status == 404:
            raise APIError("Method not found: %s" % method)
        else:
            raise APIError("Non-200 HTTP response status: %s" % response['status'])

    def login(self, user, password):
        "Login to the Eventful API as USER with PASSWORD."
        nonce = self.call('/users/login')['nonce']
        response = md5.new(nonce + ':'
                           + md5.new(password).hexdigest()).hexdigest()
        login = self.call('/users/login', user=user, nonce=nonce,
                          response=response)
        self.user_key = login['user_key']
        self.user = user
        return user
