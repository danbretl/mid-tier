from django.utils import simplejson
from django.conf import settings
from piston.emitters import Emitter, DateTimeAwareJSONEncoder

class JSONEmitterMinified(Emitter):
    """
    custom minified JSON emitter , understands timestamps.
    """
    def render(self, request):
        cb = request.GET.get('callback')
        if settings.DEBUG:
            seria = simplejson.dumps(self.construct(), cls=DateTimeAwareJSONEncoder, ensure_ascii=True, sort_keys=True, indent=4)
        else:
            seria = simplejson.dumps(self.construct(), cls=DateTimeAwareJSONEncoder, ensure_ascii=True, separators=(',',':'))

        # Callback
        if cb:
            return '%s(%s)' % (cb, seria)

        return seria
