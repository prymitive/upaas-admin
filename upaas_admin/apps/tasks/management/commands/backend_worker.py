# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import logging

from mongoengine import Q

from upaas_admin.apps.tasks.base import BackendTask
from upaas_admin.apps.tasks.daemon import DaemonCommand
from upaas_admin.apps.tasks.constants import TaskStatus


log = logging.getLogger(__name__)


class Command(DaemonCommand):

    help = 'Run backend worker'

    task_class = BackendTask

    def pop_task(self, **kwargs):
        # little magic - BackendTasks are generic but they also cover
        # PackageTask that should be serialized for
        # * local backend  - app's pkg tasks executed one after another
        # * task groups - don't start app's task if app has unfinished group
        # of tasks running
        # injecting raw mongo query to do so
        return super(Command, self).pop_task(
            backend=self.backend,
            __raw__={
                'application': {
                    '$nin': self.task_class.objects(
                        Q(is_virtual=False)
                        & (
                            Q(parent__exists=False, status=TaskStatus.running,
                                backend=self.backend)
                            | (
                                Q(parent__exists=True, parent_started=True)
                                & (
                                    Q(status__ne=TaskStatus.pending,
                                      backend=self.backend)
                                    |
                                    Q(status=TaskStatus.pending,
                                      backend__ne=self.backend)
                                )
                            )
                        )
                    ).distinct("application")}})
