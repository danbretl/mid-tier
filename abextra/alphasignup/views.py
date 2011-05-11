from django.views.generic.simple import direct_to_template
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, REDIRECT_FIELD_NAME
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.views.generic import list_detail
from django.http import HttpResponseForbidden, Http404

from userena.forms import (SignupForm, SignupFormOnlyEmail, AuthenticationForm,
                           ChangeEmailForm, EditProfileForm)
from userena.models import UserenaSignup
from userena.decorators import secure_required
from userena.backends import UserenaAuthenticationBackend
from userena.utils import signin_redirect, get_profile_model
from userena import settings as userena_settings

from guardian.decorators import permission_required_or_403

@secure_required
@permission_required_or_403('change_user', (User, 'username', 'username'))
def password_change_or_set(request, username, template_name='userena/password_form.html',
                  pass_form=PasswordChangeForm, extra_context=None):
    """ Change password of user.

    This view is almost a mirror of the view supplied in
    :func:`contrib.auth.views.password_change`, with the minor change that in
    this view we also use the username to change the password. This was needed
    to keep our URLs logical (and REST) accross the entire application. And
    that in a later stadium administrators can also change the users password
    through the web application itself.


    :param username:
      String supplying the username of the user who's password is about to be
      changed.

    :param template_name:
      String of the name of the template that is used to display the password
      change form. Defaults to ``userena/password_form.html``.

    :param pass_form:
      Form used to change password. Default is the form supplied by Django
      itself named ``SetPasswordForm``.

    :param extra_context:
      Dictionary of extra variables that are passed on the the template. The
      ``form`` key is always used by the form supplied by ``pass_form``.

    **Context**

    ``form``
      Form used to change the password.

    ``account``
      The current active account.

    """
    user = get_object_or_404(User, username__iexact=username)

    base_template = 'userena/base_userena_dual.html'

    if not user.has_usable_password():
        pass_form = SetPasswordForm
        base_template = 'userena/base_userena.html'

    form = pass_form(user=user)

    if request.method == "POST":
        form = pass_form(user=user, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse('userena_profile_detail', kwargs={'username': user.username}))

    if not extra_context:
        extra_context = dict()
    extra_context['form'] = form
    extra_context['base_template'] = base_template
    return direct_to_template(request, template_name, extra_context=extra_context)

@secure_required
def activate(request, username, activation_key,
             template_name='userena/activate_fail.html',
             extra_context=None):
    """
    Activate a user with an activation key.

    The key is a SHA1 string. When the SHA1 is found with an
    :class:`UserenaSignup`, the :class:`User` of that account will be
    activated.  After a successfull activation the view will redirect to
    ``succes_url``.  If the SHA1 is not found, the user will be shown the
    ``template_name`` template displaying a fail message.

    :param username:
        String of the username that wants to be activated.

    :param activation_key:
        String of a SHA1 string of 40 characters long. A SHA1 is always 160bit
        long, with 4 bits per character this makes it --160/4-- 40 characters
        long.

    :param template_name:
        String containing the template name that is used when the
        ``activation_key`` is invalid and the activation failes. Defaults to
        ``userena/activation_fail.html``.

    :param extra_context:
        Dictionary containing variables which could be added to the template
        context. Default to an empty dictionary.

    """
    user = UserenaSignup.objects.activate_user(username, activation_key)
    if user:
        # Sign the user in.
        auth_user = authenticate(identification=user.email,
                                 check_password=False)
        login(request, auth_user)

        if userena_settings.USERENA_USE_MESSAGES:
            messages.success(request, _('Your account has been activated! Please, set your password.'),
                             fail_silently=True)

        redirect_to = reverse('userena_password_change', kwargs={'username': username})
        return redirect(redirect_to)
    else:
        if not extra_context: extra_context = dict()
        return direct_to_template(request,
                                  template_name,
                                  extra_context=extra_context)

# =======================
# = Alpha Questionnaire =
# =======================
from alphasignup.models import AlphaQuestionnaire
from alphasignup.forms import AlphaQuestionnaireForm

@secure_required
def questionnaire(request, username, template_name='userena/questionnaire.html'):
    user = get_object_or_404(User, username__iexact=username)

    form = AlphaQuestionnaireForm()
    if request.method == "POST":
        form = AlphaQuestionnaireForm(data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,
                _('Thank you! We will let you know soon!'),
                fail_silently=True
            )
            return redirect(reverse('userena_profile_detail', kwargs={'username': user.username}))

    extra_context = dict(form=form)
    return direct_to_template(request, template_name, extra_context=extra_context)