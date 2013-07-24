# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from django.conf.urls import patterns, url

from upaas_admin.apps.admin.views import *


urlpatterns = patterns(
    'upaas_admin.apps.admin.views',
    url(r'^users$', AdminUserListView.as_view(), name='admin_users_list'),
    url(r'^users/create$', AdminCreateUserView.as_view(),
        name='admin_user_create'),
    url(r'^users/(?P<slug>[-_.\w]+)/edit$', AdminEditUserView.as_view(),
        name='admin_user_edit'),
)
