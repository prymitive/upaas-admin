# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from json import dumps

from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from dajaxice.decorators import dajaxice_register

from upaas_admin.apps.tasks.base import ApplicationTask
from upaas_admin.apps.tasks.constants import (ACTIVE_TASK_STATUSES, TaskStatus,
                                              ICON_STARTED, ICON_PENDING)


@cache_page(2)  # TODO make it configurable?
@dajaxice_register
@login_required
def user_tasks(request):
    tasks = []
    running = 0
    for task in ApplicationTask.objects(
            application__in=request.user.applications,
            status__in=ACTIVE_TASK_STATUSES):
        if task.status == TaskStatus.pending:
            icon = ICON_PENDING
        else:
            icon = ICON_STARTED
        running += 1
        tasks.append({'task_id': task.safe_id, 'title': task.title,
                      'date_created': task.date_created.isoformat(),
                      'status': task.status,
                      'progress': task.progress, 'icon': icon,
                      'application': {'name': task.application.name,
                                      'id': task.application.safe_id}})
    return dumps({'tasks': tasks, 'running': running})
