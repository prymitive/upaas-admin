# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from django.conf.urls import patterns, url

from upaas_admin.apps.applications.views import *


urlpatterns = patterns(
    'upaas_admin.apps.applications.views',
    url(r'^show/(?P<slug>[-_\w]+)$', ApplicationDetailView.as_view(),
        name='app_details'),
)
