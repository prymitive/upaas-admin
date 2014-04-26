# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import RedirectView, TemplateView

from tastypie.api import Api

from upaas_admin.apps.applications.api import (ApplicationResource,
                                               PackageResource)
from upaas_admin.apps.servers.api import (BackendResource, RouterResource)
from upaas_admin.apps.scheduler.api import RunPlanResource

from upaas_admin.apps.applications.views import IndexView

from upaas_admin.apps.users.forms import (UserPasswordChangeForm,
                                          UserPasswordSetForm)


v1_api = Api(api_name='v1')
v1_api.register(ApplicationResource())
v1_api.register(PackageResource())
v1_api.register(BackendResource())
v1_api.register(RouterResource())
v1_api.register(RunPlanResource())


handler400 = 'upaas_admin.common.handlers.bad_request'
handler403 = 'upaas_admin.common.handlers.access_denied'
handler404 = 'upaas_admin.common.handlers.page_not_found'
handler500 = 'upaas_admin.common.handlers.server_error'


urlpatterns = patterns(
    '',
    url(r'^$', IndexView.as_view(), name=IndexView.tab_id),

    url(r'^login$', 'django.contrib.auth.views.login',
        {'template_name': 'users/login.html'}, name='site_login'),
    url(r'^logout$', 'django.contrib.auth.views.logout_then_login',
        name='site_logout'),

    url(r'^password$', 'django.contrib.auth.views.password_change',
        {'template_name': 'users/password.html',
         'password_change_form': UserPasswordChangeForm}, name='password'),
    url(r'^password/changed$',
        'django.contrib.auth.views.password_change_done',
        {'template_name': 'users/password_changed.html'},
        name='password_change_done'),

    url(r'^password/reset$', 'django.contrib.auth.views.password_reset',
        {'template_name': 'users/password_reset.html',
         'email_template_name': 'users/emails/password_reset.html',
         'subject_template_name': 'users/emails/password_reset_subject.txt',
         'post_reset_redirect': 'password_reset_sent'},
        name='password_reset'),
    url(r'^password/reset/sent$', TemplateView.as_view(
        template_name='users/password_reset_sent.html'),
        name='password_reset_sent'),
    url(r'^password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$',
        'upaas_admin.common.hacks.django_password_reset.'
        'safe_password_reset_confirm',
        {'template_name': 'users/password_reset_confirm.html',
         'set_password_form': UserPasswordSetForm},
        name='password_reset_confirm'),
    url(r'^password/reset/done$', TemplateView.as_view(
        template_name='users/password_reset_complete.html'),
        name='password_reset_complete'),

    url(r'^djs/', include('djangojs.urls')),

    (r'^api/', include(v1_api.urls)),

    ('admin/', include('upaas_admin.apps.admin.urls')),
    ('applications/', include('upaas_admin.apps.applications.urls')),
    ('', include('upaas_admin.apps.users.urls')),

)


urlpatterns += staticfiles_urlpatterns()


if settings.DEBUG:
    urlpatterns += patterns(
        '',
        (r'^favicon\.ico$', RedirectView.as_view(url='/static/favicon.ico')),
    )
