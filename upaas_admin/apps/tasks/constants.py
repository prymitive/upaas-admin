# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


ICON_PENDING = 'glyphicon-time'
ICON_STARTED = 'glyphicon-cog'


class TaskStatus:
    pending = 'PENDING'
    running = 'RUNNING'
    successful = 'SUCCESSFUL'
    failed = 'FAILED'


STATUS_CHOICES = (TaskStatus.pending, TaskStatus.running,
                  TaskStatus.successful, TaskStatus.failed)
