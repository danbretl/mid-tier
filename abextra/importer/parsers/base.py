from PIL import Image
from django.conf import settings
import os
import logging
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import ValidationError
import core.utils

class BaseAdapter(object):
    logger = logging.getLogger('importer.parser')
    model_form = None
    o2m_default_field = None
    fields = []
    form_data_map, file_data_map = {}, {}
    source_name = None

    def __init__(self):
        self.model = self.model_form._meta.model
        self.cache = {}

        # reflect and process on m2o slaves
        self._slave_adapters = {}
        slave_adapters = getattr(self, 'slave_adapters', None)
        if slave_adapters:
            for form_field, adapter_cls in slave_adapters.items():
                self._slave_adapters[form_field] = adapter_cls()

        # reflect and process on o2m slaves
        self._slave_adapters_o2m = {}
        slave_adapters_o2m = getattr(self, 'slave_adapters_o2m', None)
        if slave_adapters_o2m:
            for producer, adapter_cls in slave_adapters_o2m.items():
                producer_callable = getattr(self, producer, None)
                if producer_callable:
                    self._slave_adapters_o2m[producer_callable] = adapter_cls()

    def parse(self, raw_data):
        form_data = self._adapt_form_data(raw_data, {})
        # create cache key
        key = self._cache_key(form_data)
        # try to get from cache
        created, instance = False, self.cache.get(key)
        if instance:
            self.logger.debug('MATCHED from cache %s' % str(key))

        # if cache miss, create or get from db
        if not instance:
            # try to create and validate form
            file_data = self._adapt_file_data(raw_data, {})
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
            self._post_adapt(raw_data, instance)
            # if this is a fresh instance, cache it
            if created:
                self.cache[key] = instance

        self.logger.debug((created, instance))
        return created, instance

    def _cache_key(self, form_data):
        sig_fields = self.fields or form_data.keys()
        tup = tuple(form_data.get(f) for f in sorted(sig_fields))
        self.logger.debug('field tuple %s' % str(tup))
        return hash(tup)

    def _adapt_form_data(self, raw_data, form_data):
        # set the source
        form_data['source'] = self.source_name
        form_data = self._adapt_slaves(raw_data, form_data)
        form_data = self._adapt_form_data_mappings(raw_data, form_data)
        form_data = self.adapt_form_data(raw_data, form_data)
        return form_data

    def _adapt_slaves(self, raw_data, form_data):
        for form_field, adapter in self._slave_adapters.items():
            created, obj = adapter.parse(raw_data)
            # a little presumptuous :: always django models by 'id'
            form_data[form_field] = obj.id if obj else None
        return form_data

    def _adapt_form_data_mappings(self, raw_data, form_data):
        """processes python dict paths"""
        for field, source_path in self.form_data_map.items():
            form_data[field] = core.utils.dict_path_get(raw_data, source_path)
        return form_data

    # FIXME rename into adapter_hook
    def adapt_form_data(self, raw_data, form_data):
        """hook for overrides"""
        return form_data

    # FIXME should live form-level
    def _is_valid_image(self, file_path):
        """checks the minimum dimensions of an import image"""
        image = Image.open(file_path)
        width, height = image.size
        min_dims = settings.IMPORT_IMAGE_MIN_DIMS
        return width >= min_dims['width'] and height >= min_dims['height']

    def _adapt_file_data(self, raw_data, file_data):
        for field, source_path in self.file_data_map.items():
            images = core.utils.dict_path_get(raw_data, source_path)
            if images:
                image = images[0]
                file_path = image['path']
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
        # process o2m slaves
        for producer_func, adapter in self._slave_adapters_o2m.items():
            raw_results = producer_func(raw_data)
            for raw_result in raw_results:
                raw_result[self.o2m_default_field] = instance.id
                adapter.parse(raw_result)
            # call the override hook
        self.post_adapt(raw_data, instance)

    def post_adapt(self, raw_data, instance):
        """hook for overrides"""
        pass
