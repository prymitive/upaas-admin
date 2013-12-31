# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

ICON_PENDING = 'fa fa-clock-o'
ICON_STARTED = 'fa fa-refresh fa-spin'
ICON_FAILED = 'fa fa-times-circle-o'
ICON_SUCCESSFUL = 'fa fa-check-circle-o'

# fallback icon, just in case we get unsupported string as status
ICON_UNKNOWN = 'fa fa-question-circle'


class TaskStatus:
    pending = 'PENDING'
    running = 'RUNNING'
    successful = 'SUCCESSFUL'
    failed = 'FAILED'


STATUS_CHOICES = (TaskStatus.pending, TaskStatus.running,
                  TaskStatus.successful, TaskStatus.failed)


ACTIVE_TASK_STATUSES = (TaskStatus.pending, TaskStatus.running)
FINISHED_TASKS_STATUSES = (TaskStatus.failed, TaskStatus.successful)
