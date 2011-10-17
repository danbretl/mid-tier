"""
    Yeah... Kinda stolen... Not very precious code to begin with...
    I added http pooling for work with eventlet concurrency. booya
"""

import re
import eventlet
import logging
from eventlet import pools
from eventlet.green import urllib, urllib2
from django.conf import settings
from PIL import Image
from StringIO import StringIO
import os
httplib2 = eventlet.import_patched('httplib2')
from hashlib import md5
import simplejson

IMG_SIZE_RE = re.compile('small|medium')
IMG_EXT_RE = re.compile('/(?P<name>\d+-\d+).(?P<ext>jpg|jpeg|tif|tiff|png|gif)$')

class APIError(Exception):
    pass

class API(object):
    def __init__(self, app_key, server='api.eventful.com', make_dumps=False,
            dump_sub_dir='default', img_dir=os.path.join('/tmp', settings.SCRAPE_IMAGES_PATH)):
        self.logger = logging.getLogger('importer.eventful_api')
        self.app_key = app_key
        self.server = server
        self.httpool = pools.Pool()
        self.httpool.create = httplib2.Http
        self.make_dumps = make_dumps
        parent_dump_dir = getattr(settings, 'EVENTFUL_API_DUMP_DIR', None) or 'eventful_dumps'
        self.dump_dir = os.path.join(parent_dump_dir, dump_sub_dir)

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

    # FIXME: this should go in a utils module

    def original_image_url_from_image_field(self, image_field):
        if isinstance (image_field, (tuple, list)):
            url = image_field[0]['url']
        else:
            url = image_field['url']
        if url:
            return IMG_SIZE_RE.sub('original', url)

    def image_filename_from_url(self, url, parent_id):
        matches = IMG_EXT_RE.search(url)
        if matches:
            # take first matched pattern, which is file extension
            ext = '.'+matches.groupdict()['ext']
            filename = os.path.join(self.img_dir, parent_id + ext)
            return filename

    def fetch_image(self, images_dict, parent_id):
        image_field = images_dict.get('image')
        url = self.original_image_url_from_image_field(image_field)
        if url:
            try:
                img = urllib2.urlopen(url)
            except (urllib2.URLError, urllib2.HTTPError), e:
                self.logger.info("Internets Error: %s" % url)
            else:
                img_dat = img.read()
                im = Image.open(StringIO(img_dat))
                width, height = im.size
                # FIXME: migrate image dimension checking logic to form so that it
                # can be reused
                filename = self.image_filename_from_url(url, parent_id)
                if not filename:
                    self.logger.info('Unable to parse image extension from <%s>' % url)
                else:
                    with open(filename, 'w') as f:
                        f.write(img_dat)
                    if width >= settings.IMAGE_MIN_DIMS['width'] and height >= settings.IMAGE_MIN_DIMS['height']:
                        return dict(id=parent_id, path=filename, url=url)
                    else:
                        self.logger.info('Image %s did not meet minimum image dimensions; discarding' % parent_id)

class MockAPI(API):

    def __init__(self, *args, **kwargs):
        super(MockAPI, self).__init__(*args, **kwargs)

    def fetch_image(self, images_dict, parent_id):
        image_field = images_dict.get('image')
        url = self.original_image_url_from_image_field(image_field)
        if url:
            filename = self.image_filename_from_url(url, parent_id) 
            if not filename:
                self.logger.info('Unable to parse image extension from <%s>' % url)
            else:
                if not os.path.exists(filename):
                    self.logger.info("Expected image %s not found" % filename)

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
