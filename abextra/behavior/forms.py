from django import forms
from behavior.models import EventAction

class EventActionForm(forms.ModelForm):
    class Meta:
        model = EventAction
