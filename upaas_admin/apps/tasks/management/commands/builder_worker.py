# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""

from upaas_admin.apps.applications.tasks import BuildPackageTask
from upaas_admin.apps.tasks.daemon import DaemonCommand


class Command(DaemonCommand):

    help = 'Run builder worker'

    task_class = BuildPackageTask
