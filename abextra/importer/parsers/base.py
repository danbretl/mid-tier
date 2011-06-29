import os
import logging
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
        key = self.cache_key(form_data)
        created, instance = False, self.cache.get(key)
        if not instance:
            try:
                created, instance = False, self.model.objects.get(**key._asdict())
            except self.model.DoesNotExist:
                file_data = self.parse_file_data(data, {})
                form = self.model_form(data=form_data, files=file_data)
                if form.is_valid():
                    created, instance = True, form.save(commit=True)
                else:
                    self.logger.error(form.errors)
            except self.model.MultipleObjectsReturned:
                created, instance = False, self.model.objects.filter(**key._asdict())[:1][0]
            except AttributeError:
                # This means the key did not get created correctly due to
                # missing fields
                # FIXME: Log this error
                created, instance = False, False

            if instance:
                self.cache[key] = instance
                self.post_parse(data, instance)

        result = (created, instance)
        self.logger.debug(result)
        return result

    def cache_key(self, form_data):
        try:
            return self.KeyTuple(
                **dict((f, form_data[f]) for f in self.fields if form_data.has_key(f))
                )
        except:
            # This could happen if all the necessary fields for the parser are
            # unavailable in the passed in form
            return None

    def parse_form_data(self, obj_dict, form_data={}):
        raise NotImplementedError()

    def parse_file_data(self, data, file_data):
        images = data.get('images')
        if images:
            image = images[0]
            path = os.path.join(settings.SCRAPE_FEED_PATH, settings.SCRAPE_IMAGES_PATH, image['path'])
            with open(path, 'rb') as f:
                filename = os.path.split(f.name)[1]
                file_data['image'] = SimpleUploadedFile(filename, f.read())
        return file_data

    def post_parse(self, obj_dict, instance):
        pass
