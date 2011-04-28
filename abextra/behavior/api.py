from tastypie import fields
from tastypie.resources import ModelResource
from newapi.authentication import ConsumerApiKeyAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.validation import FormValidation

from behavior.models import EventAction, User, Event
from behavior.forms import EventActionForm

from events.api import EventResource, UserResource

# ==========
# = API v1 =
# ==========
from tastypie.utils.mime import determine_format, build_content_type
from tastypie.http import HttpBadRequest
from tastypie.exceptions import ImmediateHttpResponse, NotFound
from django.core.urlresolvers import resolve, Resolver404

class EventActionResource(ModelResource):
    user = fields.ToOneField(UserResource, 'user')
    event = fields.ToOneField(EventResource, 'event')

    class Meta:
        queryset = EventAction.objects.all()
        allowed_methods = ('post',)
        detail_allowed_methods = ()
        authentication = ConsumerApiKeyAuthentication()
        authorization = DjangoAuthorization()
        validation = FormValidation(form_class=EventActionForm)

    # FIXME extremely bastardized is_valid that also creates object
    def is_valid(self, bundle, request=None):
        # prepare user id
        user_id = None
        if hasattr(request, 'user') and request.user.is_authenticated():
            user_id = request.user.id

        # prepare event id
        event_id = None
        event_uri = bundle.data.get('event')
        if event_uri:
            try:
                view, args, kwargs = resolve(event_uri)
                event_id = kwargs.get('pk')
            except Resolver404:
                raise NotFound("The URL provided '%s' was not a link to a valid resource." % event_uri)

        # prepare form with data
        form = self._meta.validation.form_class(data=dict(
            user=user_id,
            event=event_id,
            action=bundle.data.get('action', '').upper()
        ))

        # non conventional form processing
        if form.is_valid():
            instance = form.instance
            try:
                event_action = EventAction.objects.get(
                    user=instance.user, event=instance.event
                )
            except EventAction.DoesNotExist:
                event_action = instance
                event_action.save()
            else:
                if not event_action.action == instance.action:
                    event_action.action = instance.action
                    event_action.save()
            bundle.obj = event_action

        # error handling
        else:
            if request:
                desired_format = self.determine_format(request)
            else:
                desired_format = self._meta.default_format

            serialized = self.serialize(request, form.errors, desired_format)
            response = HttpBadRequest(content=serialized, content_type=build_content_type(desired_format))
            raise ImmediateHttpResponse(response=response)

    def obj_create(self, bundle, request=None, **kwargs):
        return bundle
