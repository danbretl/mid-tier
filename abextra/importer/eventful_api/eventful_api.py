"""
    Yeah... Kinda stolen... Not very precious code to begin with...
    I added http pooling for work with eventlet concurrency. booya
"""

import eventlet
from eventlet import pools
from eventlet.green import urllib, urllib2
from django.conf import settings
import os
httplib2 = eventlet.import_patched('httplib2')
from hashlib import md5
import simplejson

class APIError(Exception):
    pass

class API:
    def __init__(self, app_key, server='api.eventful.com', make_dumps=False):
        self.app_key = app_key
        self.server = server
        self.httpool = pools.Pool()
        self.httpool.create = httplib2.Http
        self.make_dumps = make_dumps
        self.dump_dir = getattr(settings, 'EVENTFUL_API_DUMP_DIR', None) or 'eventful_dumps'
        if make_dumps:
            try:
                os.mkdir(self.dump_dir)
            except OSError:
                pass

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
                json_content = simplejson.loads(content) 
                if self.make_dumps:
                    indented_content = simplejson.dumps(json_content, sort_keys=True, indent=4)
                    filename = md5(url).hexdigest() + '.json'
                    with open(os.path.join(self.dump_dir, filename), 'w') as f:
                        f.write(indented_content)
                return json_content 
            except ValueError:
                raise APIError("Unable to parse API response!")
        elif status == 404:
            raise APIError("Method not found: %s" % method)
        else:
            raise APIError("Non-200 HTTP response status: %s" % response['status'])

    def login(self, user, password):
        "Login to the Eventful API as USER with PASSWORD."
        nonce = self.call('/users/login')['nonce']
        response = md5('%(nonce)s:%(pass_digest)s' % {
                'nonce': nonce,
                'pass_digest': md5(password).hexdigest()
            }
        ).hexdigest()
        login = self.call('/users/login', user=user, nonce=nonce,
                          response=response)
        self.user_key = login['user_key']
        self.user = user
        return user
