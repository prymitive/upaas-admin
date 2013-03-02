# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from django.conf.urls import patterns
from django.views.generic import TemplateView


urlpatterns = patterns(
    'upaas_admin.apps.users.views',
    (r'^profile/my$', TemplateView.as_view()),
)
