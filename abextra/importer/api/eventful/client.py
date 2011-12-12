import re
import eventlet
import logging
import datetime
from eventlet import pools
from eventlet.green import urllib
from django.conf import settings
import os
from importer.api.eventful import conf

httplib2 = eventlet.import_patched('httplib2')
from hashlib import md5
from django.utils import simplejson

IMG_SIZE_RE = re.compile('(?<=/images/)\w+(?=/)', re.I)
IMG_EXT_RE = re.compile('/(?P<name>\d+-\d+).(?P<ext>jpg|jpeg|tif|tiff|png|gif)$', re.I)

class APIError(Exception):
    pass


class API(object):
    CALL_COUNT = 0
    logger = logging.getLogger('importer.eventful')

    def __init__(self, app_key=conf.API_KEY, server='api.eventful.com', make_dumps=False):
        self.app_key = app_key
        self.server = server
        self.httpool = pools.Pool()
        self.httpool.create = httplib2.Http
        self.make_dumps = make_dumps
        self.dump_dir = os.path.join(settings.IMPORT_ROOT_DIR, conf.IMPORT_DIR, 'dumps')
        if make_dumps and not os.path.exists(self.dump_dir):
            os.makedirs(self.dump_dir)

        # prepare image download directory
        self.img_dir = conf.IMPORT_IMAGE_DIR
        if not os.path.exists(self.img_dir):
            os.makedirs(self.img_dir)

    @staticmethod
    def daterange_query_param(start_datetime, stop_datetime):
        if not all(isinstance(dt, (datetime.datetime, datetime.date)) for dt in (start_datetime, stop_datetime)):
            raise ValueError('Inputs must be either datetimes or dates')
        format_dt = lambda dt: dt.strftime('%Y%m%d00')
        return '-'.join(map(format_dt, (start_datetime, stop_datetime)))

    @classmethod
    def daterange_query_param_by_delta(cls, start_datetime, timedelta):
        """
        Calculates date range string for eventful query based on current date and
        event horizon specified in settings.
        """
        return cls.daterange_query_param(start_datetime, start_datetime + timedelta)

    def _build_url(self, method, **args):
        """Call the Eventful API's METHOD with ARGS."""
        # Build up the request
        args['app_key'] = self.app_key
        if hasattr(self, 'user_key'):
            args['user'] = self.user
            args['user_key'] = self.user_key
        args = urllib.urlencode(args)
        return "http://%s/json/%s?%s" % (self.server, method, args)

    def _build_dump_fn(self, method, **args):
        excluded_fields = ('date',)
        dump_args = dict((k,v,) for k,v in args.iteritems() if not k in excluded_fields)
        return md5(self._build_url(method, **dump_args)).hexdigest()

    def call(self, method, **args):
        # Build the url
        url = self._build_url(method, format='json', **args)

        # Make the request
        with self.httpool.item() as http:
            self.logger.debug('%d of %d eventful API calls made so far.', self.CALL_COUNT, conf.API_CALL_LIMIT)
            self.CALL_COUNT += 1
            response, content = http.request(url, "GET")

        # Handle the response
        status = int(response['status'])
        if status == 200:
            try:
                json_content = simplejson.loads(content)
                if self.make_dumps:
                    indented_content = simplejson.dumps(json_content, sort_keys=True, indent=4)
                    filename = self._build_dump_fn(method, format='json', **args)+ '.json'
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
        url = image_field[0]['url'] if isinstance(image_field, (tuple, list)) else image_field['url']
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
        try:
            url = self._original_image_url_from_image_field(image_field)
        except (KeyError, TypeError) as e:
            self.logger.exception(e)
        else:
            try:
                filepath = self._image_filepath_from_url(url, parent_id)
            except ValueError, e:
                self.logger.exception(e)
            else:
                try:
                    output_filepath, headers = urllib.urlretrieve(url, filepath)
                except Exception, e:
                    self.logger.exception(e)
                else:
                    return dict(id=parent_id, filepath=output_filepath, url=url)


class MockAPI(API):
    def fetch_image(self, images_dict, parent_id):
        image_field = images_dict.get('image')
        try:
            url = self._original_image_url_from_image_field(image_field)
        except (KeyError, TypeError) as e:
            self.logger.exception(e)
        else:
            try:
                filepath = self._image_filepath_from_url(url, parent_id)
            except ValueError, e:
                self.logger.exception(e)
            else:
                if not os.path.exists(filepath):
                    self.logger.error("Expected image not found at path: %s", filepath)
                else:
                    return dict(id=parent_id, filepath=filepath, url=url)


    def call(self, method, **args):
        # Build the filename
        filename = self._build_dump_fn(method, format='json', **args) + '.json'
        full_path = os.path.join(self.dump_dir, filename)
        if not os.path.isfile(full_path):
            raise APIError('Could not locate necessary mock response')

        with open(full_path, 'r') as f:
            json = simplejson.load(f)
        return json
