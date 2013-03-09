# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from django.conf.urls import patterns, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import TemplateView

from django.contrib import admin


admin.autodiscover()


urlpatterns = patterns(
    '',
    (r'^$', TemplateView.as_view(template_name="index.haml")),
    (r'^login$', 'django.contrib.auth.views.login',
     {'template_name': 'login.haml'}),
    (r'^logout$', 'django.contrib.auth.views.logout_then_login'),

    (r'^', include('upaas_admin.apps.users.urls')),
)


urlpatterns += staticfiles_urlpatterns()
