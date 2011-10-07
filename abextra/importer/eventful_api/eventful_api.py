"""
    Yeah... Kinda stolen... Not very precious code to begin with...
    I added http pooling for work with eventlet concurrency. booya
"""

import eventlet
from eventlet import pools
from eventlet.green import urllib, urllib2
from django.conf import settings
from PIL import Image
from StringIO import StringIO
import os
httplib2 = eventlet.import_patched('httplib2')
from hashlib import md5
import simplejson

class APIError(Exception):
    pass

class API(object):
    def __init__(self, app_key, server='api.eventful.com', make_dumps=False, img_dir=os.path.join(settings.SCRAPE_FEED_PATH, settings.SCRAPE_IMAGES_PATH)):
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

        # prepare image download directory
        if not os.path.exists(img_dir):
            os.makedirs(img_dir)
        self.img_dir = img_dir


    def _build_url(self, method, **args):
        "Call the Eventful API's METHOD with ARGS."
        # Build up the request
        args['app_key'] = self.app_key
        if hasattr(self, 'user_key'):
            args['user'] = self.user
            args['user_key'] = self.user_key
        args = urllib.urlencode(args)
        return "http://%s/json/%s?%s" % (self.server, method, args)

    def call(self, method, **args):
        # Build the url
        url = self._build_url(method, **args)

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

    def fetch_image(self, images_dict, parent_id):
        img_dict = images_dict.get('image')
        if isinstance (img_dict, (tuple, list)):
            url = img_dict[0]['small']['url'].replace('small', 'original')
        else:
            url = img_dict['small']['url'].replace('small', 'original')
        request = urllib2.Request(url)
        try:
            img = urllib2.urlopen(request)
        except (urllib2.URLError, urllib2.HTTPError), e:
            # FIXME: use logger to print these error messages
            print "Internets Error:", url
        else:
            img_dat = img.read()
            im = Image.open(StringIO(img_dat))
            width, height = im.size
            # FIXME: migrate image dimension checking logic to form so that it
            # can be reused
            with open(filename, 'w') as f:
                f.write(img_dat)
            if width >= settings.IMAGE_MIN_DIMS['width'] and height >= settings.IMAGE_MIN_DIMS['height']:
                suffix = '.'+url.split('.')[-1]
                filename = os.path.join(self.img_dir, parent_id+suffix)
                return dict(id=parent_id, path=filename, url=url)
            else:
                print 'Image %s did not meet minimum image dimensions; discarding' % parent_id

class MockAPI(API):

    def __init__(self, *args, **kwargs):
        super(MockAPI, self).__init__(*args, **kwargs)

    def fetch_image(self, images_dict, parent_id):
        img_dict = images_dict.get('image')
        if isinstance (img_dict, (tuple, list)):
            url = img_dict[0]['small']['url'].replace('small', 'original')
        else:
            url = img_dict['small']['url'].replace('small', 'original')
        suffix = '.'+url.split('.')[-1]
        filename = os.path.join(self.img_dir, parent_id+suffix)
        if not os.path.exists(filename):
            print "Expected image %s not found" % filename
        
    def call(self, method, **args):
        # Build the url
        url = self._build_url(method, **args)

        filename = md5(url).hexdigest() + '.json'
        full_path = os.path.join(self.dump_dir, filename)
        if not os.path.isfile(full_path):
            raise APIError('Could not locate necessary mock response')

        with open(full_path, 'r') as f:
            json = simplejson.load(f)
        return json
