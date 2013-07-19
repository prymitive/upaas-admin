# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from django.conf.urls import patterns, url

from upaas_admin.apps.users.views import *


urlpatterns = patterns(
    'upaas_admin.apps.users.views',
    url(r'^profile$', UserProfileView.as_view(), name='users_profile'),
)
