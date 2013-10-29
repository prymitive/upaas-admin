# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from django.conf.urls import patterns, url

from upaas_admin.apps.applications.views import *


urlpatterns = patterns(
    'upaas_admin.apps.applications.views',
    url(r'^register$', RegisterApplicationView.as_view(),
        name='app_register'),

    url(r'^(?P<slug>[-_\w]+)/update/metadata$',
        UpdateApplicationMetadataView.as_view(), name='app_update_metadata'),
    url(r'^(?P<slug>[-_\w]+)/build$', BuildPackageView.as_view(),
        name='build_package'),

    url(r'^(?P<slug>[-_\w]+)/show$', ApplicationDetailView.as_view(),
        name=ApplicationDetailView.tab_id),
    url(r'^(?P<slug>[-_\w]+)/metadata$', ApplicationMetadataView.as_view(),
        name=ApplicationMetadataView.tab_id),
    url(r'^(?P<slug>[-_\w]+)/packages$', ApplicationPackagesView.as_view(),
        name=ApplicationPackagesView.tab_id),
    url(r'^(?P<slug>[-_\w]+)/instances$', ApplicationInstancesView.as_view(),
        name=ApplicationInstancesView.tab_id),
    url(r'^(?P<slug>[-_\w]+)/tasks$', ApplicationTasksView.as_view(),
        name=ApplicationTasksView.tab_id),

    url(r'^(?P<slug>[-_\w]+)/start$', StartApplicationView.as_view(),
        name='app_start'),
    url(r'^(?P<slug>[-_\w]+)/stop$', StopApplicationView.as_view(),
        name='app_stop'),

    url(r'^pkg/(?P<slug>[-_\w]+)$', PackageDetailView.as_view(),
        name='package_details'),
    url(r'^pkg/(?P<slug>[-_\w]+)/rollback$', RollbackApplicationView.as_view(),
        name='package_rollback'),
)
