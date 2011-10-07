import os
import logging
from itertools import chain
from collections import namedtuple
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import ValidationError

class BaseParser(object):
    logger = logging.getLogger('importer.parser')
    model_form = None
    fields = []
    img_dict_key = 'image_local' 

    def __init__(self):
        self.model = self.model_form._meta.model
        self.KeyTuple = namedtuple('KeyTuple', self.fields)
        self.cache = {}

    def parse(self, data):
        form_data = self.parse_form_data(data, {})
        # create cache key
        key = self.cache_key(form_data)
        # try to get from cache
        created, instance = False, self.cache.get(key)
        if instance:
            self.logger.debug('MATCHED from cache %s' % str(key))

        # if cache miss, create or get from db
        if not instance:
            # try to create and validate form
            file_data = self.parse_file_data(data, {})
            form = self.model_form(data=form_data, files=file_data)
            if form.is_valid():
                # now that the form has been cleaned and the data in it has
                # been marshalled, we can ask the db if it has a match
                sig_fields = self.fields or form.fields.keys()
                attrs = dict((f, getattr(form.instance, f)) for f in sig_fields)
                try:
                    created, instance = False, self.model.objects.get(**attrs)
                    self.logger.debug('MATCHED FROM DB' + str(attrs.keys()))
                except self.model.DoesNotExist:
                    created, instance = False, None

                # if we didn't find a db match, let's try to save the form
                if not instance:
                    created, instance = True, form.save(commit=True)
            else:
                # could be invalid, because already exists in db
                try:
                    form.instance.validate_unique()
                # indeed, it happened due to uniqueness constraints
                except ValidationError:
                    sig_fields = self.fields or form.fields.keys()
                    attrs = dict((f, getattr(form.instance, f)) for f in sig_fields)
                    created, instance = False, self.model.objects.get(**attrs)
                    self.logger.debug('MATCHED FROM DB' + str(attrs.keys()))

                # form is invalid due to bad data, create nothing
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
        sig_fields = self.fields or form_data.keys()
        tup = tuple(form_data.get(f) for f in sorted(sig_fields))
        self.logger.debug('field tuple %s' % str(tup))
        return hash(tup)

    def parse_form_data(self, obj_dict, form_data):
        raise NotImplementedError()

    def parse_file_data(self, data, file_data):
        
        images = data.get(self.img_dict_key)
        if images:
            image = images[0]
            path = os.path.join(settings.SCRAPE_FEED_PATH, settings.SCRAPE_IMAGES_PATH, image['path'])
            with open(path, 'rb') as f:
                filename = os.path.split(f.name)[1]
                file_data['image'] = SimpleUploadedFile(filename, f.read())
        return file_data

    def post_parse(self, obj_dict, instance):
        pass
