# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from upaas_admin.apps.applications.models import Application


class OwnedAppsMixin(object):

    def get_queryset(self):
        return Application.objects.filter(owner=self.request.user)
