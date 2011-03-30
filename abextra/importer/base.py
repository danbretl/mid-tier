from collections import namedtuple

class BaseParser(object):
    def __init__(self):
        self.model = self.model_form._meta.model
        self.key_tuple = namedtuple('key_tuple', self.fields)
        self.cache = {}

    def parse(self, data):
        form_data = self.parse_form_data(data)
        key = self.cache_key(form_data)
        created, instance = False, self.cache.get(key)
        if not instance:
            try:
                created, instance = False, self.model.objects.get(**key._asdict())
            except self.model.DoesNotExist:
                form = self.model_form(form_data)
                if form.is_valid():
                    created, instance = True, form.save(commit=True)
            if instance:
                self.cache[key] = instance
        return created, instance

    def cache_key(self, form_data):
        return self.key_tuple(
            **dict((f, form_data[f]) for f in self.fields if form_data.has_key(f))
        )

    def parse_form_data(self, obj_dict):
        raise NotImplementedError()
