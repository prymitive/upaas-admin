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
        name=ApplicationDetailView.tab_id),
    url(r'^register$', RegisterApplicationView.as_view(),
        name='app_register'),
    url(r'^start/(?P<slug>[-_\w]+)$', StartApplicationView.as_view(),
        name='app_start'),
    url(r'^packages/(?P<slug>[-_\w]+)$', ApplicationPackagesView.as_view(),
        name=ApplicationPackagesView.tab_id),
    url(r'^instances/(?P<slug>[-_\w]+)$', ApplicationInstancesView.as_view(),
        name=ApplicationInstancesView.tab_id),
)
