import os
import logging
from itertools import chain
from collections import namedtuple
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

class BaseParser(object):
    logger = logging.getLogger('importer.parser')

    def __init__(self):
        self.model = self.model_form._meta.model
        self.KeyTuple = namedtuple('KeyTuple', self.fields)
        self.cache = {}

    def parse(self, data):
        form_data = self.parse_form_data(data, {})

        # try to create and validate form
        file_data = self.parse_file_data(data, {})
        form = self.model_form(data=form_data, files=file_data)
        valid = form.is_valid()
        if valid:
            # create cache key
            key = self.cache_key(form.cleaned_data)
            # try cache
            created, instance = False, self.cache.get(key)
            # if not in the cache, save the form
            if not instance:
                created, instance = True, form.save(commit=True)
                self.cache[key] = instance
        else:
            # could be invalid, because already exists in db
            flat_errors = chain.from_iterable(form.errors.itervalues())
            if any('already exists' in e for e in flat_errors):
                key_dict = dict((f, getattr(form.instance, f)) for f in form.fields.iterkeys())
                key = self.cache_key(key_dict)
                created, instance = False, self.model.objects.get(**key._asdict())
            # form is invalid due to data validation reasons
            else:
                self.logger.error(form.errors)
                created, instance = False, None

        # if we have an instance, do a post parse
        if instance:
            self.post_parse(data, instance)
            # if this is a fresh instance, cache it
            if created:
                self.cache[key] = instance

        self.logger.debug((created, instance))
        return created, instance 

    def cache_key(self, form_data):
        try:
            kwargs = dict((f, form_data[f]) for f in self.fields)
        except KeyError:
            self.logger.warn("Can't create key given %s" % str(form_data))
            return None
        else:
            return self.KeyTuple(**kwargs)

    def parse_form_data(self, obj_dict, form_data={}):
        raise NotImplementedError()

    def parse_file_data(self, data, file_data):
        # images = data.get('images')
        # if images:
            # image = images[0]
            # path = os.path.join(settings.SCRAPE_FEED_PATH, settings.SCRAPE_IMAGES_PATH, image['path'])
            # with open(path, 'rb') as f:
                # filename = os.path.split(f.name)[1]
                # file_data['image'] = SimpleUploadedFile(filename, f.read())
        # return file_data
        pass

    def post_parse(self, obj_dict, instance):
        pass
