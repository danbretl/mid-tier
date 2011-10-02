import logging
from itertools import chain
from collections import namedtuple

class BaseParser(object):
    logger = logging.getLogger('importer.parser')
    model_form = None
    fields = []

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

        # if cache miss, create or get from db
        if not instance:
            # try to create and validate form
            file_data = self.parse_file_data(data, {})
            form = self.model_form(data=form_data, files=file_data)
            if form.is_valid():
                created, instance = True, form.save(commit=True)
            else:
                # could be invalid, because already exists in db
                flat_errors = chain.from_iterable(form.errors.itervalues())
                if any('already exists' in e.lower() for e in flat_errors):
                    attrs = dict((f, getattr(form.instance, f)) for f in form.fields.iterkeys())
                    created, instance = False, self.model.objects.get(**attrs)
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
        return hash(tup)

    def parse_form_data(self, obj_dict, form_data):
        raise NotImplementedError()

    def parse_file_data(self, data, file_data):
        pass

    def post_parse(self, obj_dict, instance):
        pass
