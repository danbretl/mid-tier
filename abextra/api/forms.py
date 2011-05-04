import re
from django import forms
from models import DeviceUdid

# simulator udid: 12345678-1234-1234-123456789ABC (hex)
# iphone udid: 40digits (hex)
UDID_RE = re.compile(r'([0-9A-F]{8}(-[0-9A-F]{4}){3}-[0-9A-F]{12})|([0-9A-F]{40})', re.I)

class DeviceUdidForm(forms.ModelForm):
    udid = forms.RegexField(regex=UDID_RE)

    class Meta:
        model = DeviceUdid

    def clean_udid(self):
        raw_udid = self.cleaned_data['udid']
        return DeviceUdid.objects.get_hexdigest(raw_udid)
