# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals


ICON_STARTED = 'fa fa-refresh fa-spin'
ICON_FAILED = 'fa fa-times-circle-o text-danger'
ICON_SUCCESSFUL = 'fa fa-check-circle-o text-success'

# fallback icon, just in case we get unsupported string as status
ICON_UNKNOWN = 'fa fa-question-circle'


class TaskStatus:
    running = 'RUNNING'
    successful = 'SUCCESSFUL'
    failed = 'FAILED'


STATUS_CHOICES = (TaskStatus.running, TaskStatus.successful, TaskStatus.failed)
