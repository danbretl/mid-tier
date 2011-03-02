class PreprocessRouter(object):
    """A router to control all database operations on models in
    the `preprocess` application to the `scrape` db"""

    app_name = 'preprocess'
    db_name = 'scrape'

    def db_for_read(self, model, **hints):
        "Point all operations on `preprocess` models to `scrape`"
        if model._meta.app_label == self.app_name:
            return self.db_name
        return None

    def db_for_write(self, model, **hints):
        "Point all operations on `preprocess` models to `scrape`"
        if model._meta.app_label == self.app_name:
            return self.db_name
        return None

    def allow_relation(self, obj1, obj2, **hints):
        "Allow any relation if a model in `preprocess` is involved"
        if obj1._meta.app_label == self.app_name or obj2._meta.app_label == self.app_name:
            return True
        return None

    def allow_syncdb(self, db, model):
        "Make sure the `preprocess` app only appears on the `scrape` db"
        if db == self.db_name:
            return model._meta.app_label == self.app_name
        elif model._meta.app_label == self.app_name:
            return False
        return None
