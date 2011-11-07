from django.forms.models import ModelForm

class ImportFormMux(object):
    def _post_clean(self):
        self._validate_unique = False
        form_base = self.__class__.__bases__[1]
        if not issubclass(form_base, ModelForm):
            raise TypeError('Import forms must inherit from ModelForm')
        form_base._post_clean(self)
