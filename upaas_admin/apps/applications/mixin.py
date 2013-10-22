# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from upaas_admin.apps.applications.models import Application, Package


class OwnedAppsMixin(object):
    """
    Limits query to applications owned by current user.
    """

    def get_queryset(self):
        return Application.objects.filter(owner=self.request.user)


class OwnedPackagesMixin(object):
    """
    Limits query to packages belonging to apps owned by current user.
    """

    def get_queryset(self):
        return Package.objects.filter(
            application__in=Application.objects.filter(
                owner=self.request.user))
