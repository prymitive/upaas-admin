# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from django.conf.urls import patterns, url

from upaas_admin.apps.admin.views import *


urlpatterns = patterns(
    'upaas_admin.apps.admin.views',

    url(r'^users$', AdminUserListView.as_view(), name='admin_users_list'),
    url(r'^users/create$', AdminCreateUserView.as_view(),
        name='admin_user_create'),
    url(r'^users/(?P<slug>[-_.\w]+)/edit$', AdminEditUserView.as_view(),
        name='admin_user_edit'),

    url(r'^users/limits/(?P<slug>[-_.\w]+)/create$',
        AdminCreateUserLimitsView.as_view(), name='admin_user_limits_create'),
    url(r'^users/limits/(?P<slug>[-_.\w]+)/edit$',
        AdminEditUserLimitsView.as_view(), name='admin_user_limits_edit'),
    url(r'^users/limits/(?P<slug>[-_.\w]+)/delete$',
        AdminDeleteUserLimitsView.as_view(), name='admin_user_limits_delete'),

    url(r'^routers$', AdminRouterListView.as_view(),
        name='admin_routers_list'),
    url(r'^routers/create$', AdminCreateRouterView.as_view(),
        name='admin_router_create'),
    url(r'^routers/(?P<slug>[-_.\w]+)/edit$', AdminEditRouterView.as_view(),
        name='admin_router_edit'),

    url(r'^backends$', AdminBackendListView.as_view(),
        name='admin_backends_list'),
    url(r'^backends/create$', AdminCreateBackendView.as_view(),
        name='admin_backend_create'),
    url(r'^backends/(?P<slug>[-_.\w]+)/edit$', AdminEditBackendView.as_view(),
        name='admin_backend_edit'),
)
