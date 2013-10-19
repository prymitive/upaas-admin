# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""

from upaas_admin.apps.applications.tasks import BuildPackageTask
from upaas_admin.apps.tasks.daemon import DaemonCommand
from upaas_admin.apps.tasks.constants import TaskStatus


class Command(DaemonCommand):

    help = 'Run builder worker'

    task_class = BuildPackageTask

    def pop_task(self, **kwargs):
        return super(Command, self).pop_task(
            application__nin=[t.application for t in BuildPackageTask.objects(
                status=TaskStatus.running)])
