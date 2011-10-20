import re
import eventlet
import logging
from eventlet import pools
from eventlet.green import urllib, urllib2
from django.conf import settings
import os
from importer.conf import get_import_image_dir
httplib2 = eventlet.import_patched('httplib2')
from hashlib import md5
import simplejson

IMG_SIZE_RE = re.compile('(?<=/images/)\w+(?=/)', re.I)
IMG_EXT_RE = re.compile('/(?P<name>\d+-\d+).(?P<ext>jpg|jpeg|tif|tiff|png|gif)$', re.I)

class APIError(Exception):
    pass


class API(object):
    def __init__(self, app_key, server='api.eventful.com', make_dumps=False, dump_sub_dir=None):
        self.logger = logging.getLogger('importer.eventful')
        self.app_key = app_key
        self.server = server
        self.httpool = pools.Pool()
        self.httpool.create = httplib2.Http
        self.make_dumps = make_dumps
        if make_dumps and not dump_sub_dir:
            raise ValueError('dump_sub_dir is required when making dumps ;)')

        self.dump_dir = os.path.join(settings.EVENTFUL_CLIENT_DUMP_DIR, dump_sub_dir)
        if make_dumps:
            if not os.path.exists(self.dump_dir):
                os.makedirs(self.dump_dir)

        # prepare image download directory
        self.img_dir = get_import_image_dir('eventful')
        if not os.path.exists(self.img_dir):
            os.makedirs(self.img_dir)

    def _build_url(self, method, **args):
        """Call the Eventful API's METHOD with ARGS."""
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
        """Login to the Eventful API as USER with PASSWORD."""
        nonce = self.call('/users/login')['nonce']
        response = md5('%(nonce)s:%(pass_digest)s' % {
            'nonce': nonce,
            'pass_digest': md5(password).hexdigest()
        }).hexdigest()
        login = self.call('/users/login', user=user, nonce=nonce,
                          response=response)
        self.user_key = login['user_key']
        self.user = user
        return user

    # FIXME: this should go in a utils module

    def _original_image_url_from_image_field(self, image_field):
        if isinstance(image_field, (tuple, list)):
            url = image_field[0]['url']
        else:
            url = image_field['url']
        if url:
            return IMG_SIZE_RE.sub('original', url)

    def _image_filepath_from_url(self, url, parent_id):
        matches = IMG_EXT_RE.search(url)
        if not matches:
            raise ValueError('No <filename.extension> could be found in url %s:' % url)
        ext = matches.groupdict()['ext']
        filename = '.'.join((parent_id, ext))
        return os.path.join(self.img_dir, filename)

    def fetch_image(self, images_dict, parent_id):
        image_field = images_dict.get('image')
        url = self._original_image_url_from_image_field(image_field)
        if url:
            try:
                img = urllib2.urlopen(url)
            except (urllib2.URLError, urllib2.HTTPError), e:
                self.logger.exception(e)
            else:
                filepath = self._image_filepath_from_url(url, parent_id)
                if not filepath:
                    self.logger.error('Unable to produce filepath from url: %s', url)
                else:
                    with open(filepath, 'wb') as f:
                        f.write(img.read())
                        return dict(id=parent_id, filepath=f.name, url=url)


class MockAPI(API):
    def __init__(self, *args, **kwargs):
        super(MockAPI, self).__init__(*args, **kwargs)

    def fetch_image(self, images_dict, parent_id):
        image_field = images_dict.get('image')
        url = self._original_image_url_from_image_field(image_field)
        if url:
            try:
                filepath = self._image_filepath_from_url(url, parent_id)
            except ValueError, e:
                self.logger.exception(e)
            else:
                if not os.path.exists(filepath):
                    self.logger.error("Expected image not found at path: %s", filepath)
                return dict(id=parent_id, filepath=filepath, url=url)


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
