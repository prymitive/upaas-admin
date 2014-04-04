# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from upaas_admin.apps.applications.models import Application
from upaas_admin.apps.applications.constants import ApplicationFlags
from upaas_admin.apps.applications.tasks import BuildPackageTask


def builder_mule():
    while True:
        app = Application.objects(
            flags=ApplicationFlags.needs_building).first()
        if app:
            fresh = app.flags.get(ApplicationFlags.build_fresh_package)
            interpreter_version = app.flags.get(ApplicationFlags.needs_building)



if __name__ == '__main__':
    builder_mule()
