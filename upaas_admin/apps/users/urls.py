# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from django.conf.urls import patterns

from upaas_admin.apps.users.views import *


urlpatterns = patterns(
    'upaas_admin.apps.users.views',
    (r'^profile/my$', UserProfileView.as_view()),
)
