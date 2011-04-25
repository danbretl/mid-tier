from django import forms
from behavior.models import EventAction


class EventActionForm(forms.ModelForm):
    class Meta:
        model = EventAction

    # FIXME shameless hack to circumvent form validation for event actions api
    def validate_unique(self):
        exclude = self._get_validation_exclusions()
        exclude.append('action') # allow checking against the missing attribute
        exclude.append('event') # allow checking against the missing attribute

        try:
            self.instance.validate_unique(exclude=exclude)
        except forms.ValidationError, e:
            self._update_errors(e.message_dict)
