# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import RedirectView

from dajaxice.core import dajaxice_autodiscover, dajaxice_config

from tastypie.api import Api

from upaas_admin.apps.applications.api import (ApplicationResource,
                                               PackageResource)
from upaas_admin.apps.servers.api import (BackendResource, RouterResource)
from upaas_admin.apps.scheduler.api import RunPlanResource

from upaas_admin.apps.applications.views import IndexView
from upaas_admin.apps.tasks.registry import tasks_autodiscover

from upaas_admin.apps.users.forms import UserPasswordChangeForm


v1_api = Api(api_name='v1')
v1_api.register(ApplicationResource())
v1_api.register(PackageResource())
v1_api.register(BackendResource())
v1_api.register(RouterResource())
v1_api.register(RunPlanResource())


dajaxice_autodiscover()

tasks_autodiscover()


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
        name='password_changed'),

    url(r'^djs/', include('djangojs.urls')),
    url(dajaxice_config.dajaxice_url, include('dajaxice.urls')),

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
