from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse

from userena import views as userena_views
from userena import settings as userena_settings

from alphasignup import views as alpha_views
from alphasignup.forms import AlphaSignupForm, EditProfileAlphaForm


urlpatterns = patterns('',
    # Signup, signin and signout
    url(r'^signup/$',
       alpha_views.signup,
       {'signup_form': AlphaSignupForm},
       name='userena_signup'
    ),
    url(r'^signin/$',
       userena_views.signin,
       name='userena_signin'),
    url(r'^signout/$',
       auth_views.logout,
       {'next_page': userena_settings.USERENA_REDIRECT_ON_SIGNOUT,
        'template_name': 'userena/signout.html'},
       name='userena_signout'),

    # Reset password
    url(r'^password/reset/$',
       auth_views.password_reset,
       {'template_name': 'userena/password_reset_form.html',
        'email_template_name': 'userena/emails/password_reset_message.txt'},
       name='userena_password_reset'),
    url(r'^password/reset/done/$',
       auth_views.password_reset_done,
       {'template_name': 'userena/password_reset_done.html'},
       name='userena_password_reset_done'),
    url(r'^password/reset/confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
       auth_views.password_reset_confirm,
       {'template_name': 'userena/password_reset_confirm_form.html'},
       name='userena_password_reset_confirm'),
    url(r'^password/reset/confirm/complete/$',
       auth_views.password_reset_complete,
       {'template_name': 'userena/password_reset_complete.html'}),


    # Signup
    url(r'^(?P<username>\w+)/signup/complete/$',
       userena_views.direct_to_user_template,
       {'template_name': 'userena/signup_complete.html',
        'extra_context': {'userena_activation_days': userena_settings.USERENA_ACTIVATION_DAYS}},
       name='userena_signup_complete'),

    # Activate
    url(r'^(?P<username>\w+)/activate/complete/$',
        userena_views.direct_to_user_template,
        {'template_name': 'userena/activate_complete.html'},
        name='userena_activate_complete'
    ),
        url(r'^(?P<username>\w+)/activate/(?P<activation_key>\w+)/$',
        alpha_views.activate,
        name='userena_activate'
    ),

    # Change email and confirm it
    url(r'^(?P<username>\w+)/email/$',
       userena_views.email_change,
       name='userena_email_change'),
    url(r'^(?P<username>\w+)/email/complete/$',
       userena_views.direct_to_user_template,
       {'template_name': 'userena/email_change_complete.html'},
       name='userena_email_change_complete'),
    url(r'^(?P<username>\w+)/confirm-email/complete/$',
       userena_views.direct_to_user_template,
       {'template_name': 'userena/email_confirm_complete.html'},
       name='userena_email_confirm_complete'),
    url(r'^(?P<username>\w+)/confirm-email/(?P<confirmation_key>\w+)/$',
       userena_views.email_confirm,
       name='userena_email_confirm'),

    # Disabled account
    url(r'^(?P<username>\w+)/disabled/$',
       userena_views.direct_to_user_template,
       {'template_name': 'userena/disabled.html'},
       name='userena_disabled'),

    # Change or Set Password
    url(r'^(?P<username>\w+)/password/$',
       alpha_views.password_change_or_set,
       name='userena_password_change'
    ),

    url(r'^(?P<username>\w+)/password/complete/$',
       userena_views.direct_to_user_template,
       {'template_name': 'userena/password_complete.html'},
       name='userena_password_change_complete'),

    # Edit profile
    url(r'^(?P<username>\w+)/edit/$',
       userena_views.profile_edit,
       {'edit_profile_form': EditProfileAlphaForm},
       name='userena_profile_edit'),

    # View profiles
    url(r'^(?P<username>\w+)/$',
       alpha_views.profile_detail,
       name='userena_profile_detail'),
    # url(r'^page/(?P<page>[0-9]+)/$',
    #    userena_views.profile_list,
    #    name='userena_profile_list_paginated'),
    # url(r'^$',
    #    userena_views.profile_list,
    #    name='userena_profile_list'),
)

urlpatterns += patterns('',
    url(r'^(?P<username>\w+)/questionnaire/$',
        alpha_views.questionnaire,
        name='alpha_questionnaire'
    ),
    url(r'^(?P<username>\w+)/download/$',
        alpha_views.download,
        name='alpha_download'
    ),
    url(r'^(?P<username>\w+)/udid/$',
        alpha_views.device_udid,
        name='alpha_udid'
    ),
)