# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from django.conf.urls import patterns, url

from upaas_admin.apps.applications.views import *


urlpatterns = patterns(
    'upaas_admin.apps.applications.views',
    url(r'^register$', RegisterApplicationView.as_view(),
        name=RegisterApplicationView.tab_id),

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
    url(r'^(?P<slug>[-_\w]+)/stats$', ApplicationStatsView.as_view(),
        name=ApplicationStatsView.tab_id),
    url(r'^(?P<slug>[-_\w]+)/tasks$', ApplicationTasksView.as_view(),
        name=ApplicationTasksView.tab_id),
    url(r'^(?P<slug>[-_\w]+)/domains$',
        ApplicationDomainsView.as_view(), name=ApplicationDomainsView.tab_id),

    url(r'^(?P<slug>[-_\w]+)/domains/assign$',
        AssignApplicationDomainView.as_view(), name='app_assign_domain'),
    url(r'^domains/remove/(?P<slug>[-_\w]+)$',
        RemoveApplicationDomainView.as_view(), name='app_remove_domain'),

    url(r'^(?P<slug>[-_\w]+)/start$', StartApplicationView.as_view(),
        name='app_start'),
    url(r'^(?P<slug>[-_\w]+)/edit$', EditApplicationRunPlanView.as_view(),
        name='app_edit_run_plan'),
    url(r'^(?P<slug>[-_\w]+)/stop$', StopApplicationView.as_view(),
        name='app_stop'),

    url(r'^pkg/(?P<slug>[-_\w]+)$', PackageDetailView.as_view(),
        name='package_details'),
    url(r'^pkg/(?P<slug>[-_\w]+)/rollback$', RollbackApplicationView.as_view(),
        name='package_rollback'),
    url(r'^pkg/(?P<slug>[-_\w]+)/metadata/restore$',
        ApplicatiomMetadataFromPackageView.as_view(),
        name='app_meta_from_pkg'),
    url(r'^pkg/(?P<slug>[-_\w]+)/delete$', PackageDeleteView.as_view(),
        name='package_delete'),

    url(r'^(?P<slug>[-_\w]+)/metadata.yml$',
        DownloadApplicationMetadataView.as_view(), name='app_metadata_yml'),
    url(r'^pkg/(?P<slug>[-_\w]+)/metadata.yml$',
        DownloadPackageMetadataView.as_view(), name='pkg_metadata_yml'),

    url(r'^task/(?P<slug>[-_\w]+)$', ApplicationTaskDetailsView.as_view(),
        name='app_task_details'),
)
