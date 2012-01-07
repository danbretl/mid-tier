from PIL import Image
from django.conf import settings
import os
import logging
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import ValidationError
import core.utils

class BaseAdaptor(object):
    logger = logging.getLogger('importer.adaptor')
    model_form = None
    fields = []
    form_data_map, file_data_map = {}, {}
    source_name = None
    slave_adaptors = {}
    slave_adaptors_to_many = []

    def __init__(self):
        self.model = self.model_form._meta.model
        self.cache = {}

        # instantiate 'foreign relation' slaves
        self._slave_adaptors = {}
        for form_field, adaptor_cls in self.slave_adaptors.iteritems():
            self._slave_adaptors[form_field] = adaptor_cls()

        # instantiate 'o2m and m2m' slaves
        self._slave_adaptors_to_many = []
        for adaptor_cls in self.slave_adaptors_to_many:
            self._slave_adaptors_to_many.append(adaptor_cls())

    def adapt(self, raw_data):
        form_data, file_data = self._adapt_form_data(raw_data), self._adapt_file_data(raw_data)
        return self._adapt(raw_data, form_data, file_data)

    def adapt_m2o(self, raw_data, **kwargs):
        form_data_generator = self.adapt_form_data_many(raw_data)
        results = []
        for form_data in form_data_generator:
            self._adapt_form_data(raw_data, form_data)
            form_data.update(**kwargs)
            # FIXME not handling any form media :: passing empty file_data
            results.append(self._adapt(raw_data, form_data, {}))
        return results

    def _adapt(self, raw_data, form_data, file_data):
        # try to get from cache, else create of get from db
#        key = self._cache_key(form_data)
#        created, instance = False, self.cache.get(key)
        created, instance = False, None    # caching is dangerous, if rollbacks possible via transactions or manually
        if instance:
            self.logger.debug('%s matched from cache with pk: %i', self.model._meta.object_name, instance.pk)
        else:
            # try to create and validate form
            form = self.model_form(data=form_data, files=file_data)
            if form.is_valid():
                # now that the form has been cleaned and the data in it has
                # been marshalled, we can ask the db if it has a match
                sig_fields = self.fields or form.fields.keys()
                attrs = dict((f, getattr(form.instance, f)) for f in sig_fields)
                try:
                    created, instance = False, self.model.objects.get(**attrs)
                    self.logger.debug('%s matched from db with pk: %i', self.model._meta.object_name, instance.pk)
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
                    self.logger.debug('%s matched from db with pk: %i', self.model._meta.object_name, instance.pk)
                # form is invalid due to bad data, create nothing
                else:
                    self.logger.error('%s form data invalid:\n%s', self.model._meta.object_name, form.errors.as_text())
                    created, instance = False, None

        # if we have an instance, do a post adapt
        if instance:
            self._post_adapt(raw_data, instance)
            # if this is a fresh instance, cache it
#            if created:
#                self.cache[key] = instance

        self.logger.debug((created, instance))
        return created, instance

    def _cache_key(self, form_data):
        sig_fields = self.fields or form_data.keys()
        tup = tuple(form_data.get(f) for f in sorted(sig_fields))
        self.logger.debug('field tuple %s' % str(tup))
        return hash(tup)

    def _adapt_form_data(self, raw_data, form_data=None):
        form_data = form_data or {}
        form_data['source'] = self.source_name
        form_data = self._adapt_slaves(raw_data, form_data)
        form_data = self._adapt_form_data_mappings(raw_data, form_data)
        form_data = self.adapt_form_data(raw_data, form_data)
        return form_data

    def adapt_form_data(self, raw_data, form_data):
        """hook for overrides"""
        return form_data

    def adapt_form_data_many(self, raw_data):
        """abstract generator of form data(s)"""
        raise NotImplementedError('Must be implemented on the specific adaptor')

    # foreign relatives
    def _adapt_slaves(self, raw_data, form_data):
        for form_field, adaptor in self._slave_adaptors.items():
            created, obj = adaptor.adapt(raw_data)
            # a little presumptuous :: always django models by 'id'
            form_data[form_field] = obj.id if obj else None
        return form_data

    def _adapt_form_data_mappings(self, raw_data, form_data):
        """processes python dict paths"""
        for field, source_path in self.form_data_map.items():
            form_data[field] = core.utils.dict_path_get(raw_data, source_path)
        return form_data

    # FIXME should live form-level
    def _is_valid_image(self, file_path):
        """checks the minimum dimensions of an import image"""
        image = Image.open(file_path)
        width, height = image.size
        min_dims = settings.IMPORT_IMAGE_MIN_DIMS
        return width >= min_dims['width'] and height >= min_dims['height']

    def _adapt_file_data(self, raw_data):
        file_data = {}
        for field, source_path in self.file_data_map.items():
            images = core.utils.dict_path_get(raw_data, source_path)
            if images:
                image = images[0]
                file_path = image['filepath']
                if os.path.exists(file_path):
                    if self._is_valid_image(file_path):
                        with open(file_path, 'rb') as f:
                            file_name = os.path.basename(f.name)
                            file_data[field] = SimpleUploadedFile(file_name, f.read())
                    else:
                        self.logger.info('Image %s did not meet minimum image dimensions; discarding' % file_path)
        return self.adapt_file_data(raw_data, file_data)

    def adapt_file_data(self, raw_data, file_data):
        """hook for overrides"""
        return file_data

    def _post_adapt(self, raw_data, instance):
        # process 'o2m and m2m' slaves
        for adaptor in self._slave_adaptors_to_many:
            adaptor.adapt_m2o(raw_data, **{self.model._meta.module_name: instance.id})
        # call the override hook
        self.post_adapt(raw_data, instance)

    def post_adapt(self, raw_data, instance):
        """hook for overrides"""
        pass
