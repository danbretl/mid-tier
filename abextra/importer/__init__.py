from django.forms.models import ModelFormMetaclass

class ImportFormMetaClass(ModelFormMetaclass):
    """This metaclass makes sure that a ModelForm does not validate uniqueness"""
    def __new__(cls, name, bases, attrs):
        new_class = super(ImportFormMetaClass, cls).__new__(cls, name, bases, attrs)
        def clean(self):
            cleaned_data = self._original_clean()
            self._validate_unique = False
            return cleaned_data
        new_class._original_clean = new_class.clean
        new_class.clean = clean
        return new_class
