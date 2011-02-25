from django.utils import simplejson
from piston.emitters import Emitter, DateTimeAwareJSONEncoder

class JSONEmitterMinified(Emitter):
    """
    custom minified JSON emitter , understands timestamps.
    """
    def render(self, request):
        cb = request.GET.get('callback')
        seria = simplejson.dumps(self.construct(), cls=DateTimeAwareJSONEncoder, ensure_ascii=False)

        # Callback
        if cb:
            return '%s(%s)' % (cb, seria)

        return seria
