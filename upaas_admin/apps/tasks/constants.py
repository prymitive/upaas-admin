# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


ICON_PENDING = 'glyphicon-time'
ICON_STARTED = 'glyphicon-cog'
ICON_FAILED = 'glyphicon-remove-circle'
ICON_SUCCESSFUL = 'glyphicon-ok-circle'


class TaskStatus:
    pending = 'PENDING'
    running = 'RUNNING'
    successful = 'SUCCESSFUL'
    failed = 'FAILED'


STATUS_CHOICES = (TaskStatus.pending, TaskStatus.running,
                  TaskStatus.successful, TaskStatus.failed)


ACTIVE_TASK_STATUSES = (TaskStatus.pending, TaskStatus.running)
FINISHED_TASKS_STATUSES = (TaskStatus.failed, TaskStatus.successful)
