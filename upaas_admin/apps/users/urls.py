# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from django.conf.urls import patterns, url

from upaas_admin.apps.users.views import *


urlpatterns = patterns(
    'upaas_admin.apps.users.views',
    url(r'^profile$', UserProfileView.as_view(), name='users_profile'),
    url(r'^apikey/reset$', ResetApiKeyView.as_view(),
        name='users_apikey_reset'),
    url(r'^limits$', UserLimitsView.as_view(), name=UserLimitsView.tab_id),
    url(r'^tasks$', UserTasksView.as_view(), name=UserTasksView.tab_id),
)
