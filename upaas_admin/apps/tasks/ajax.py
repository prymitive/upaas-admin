# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from datetime import datetime, timedelta
from json import dumps

from mongoengine import Q

from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from dajaxice.decorators import dajaxice_register

from upaas_admin.apps.tasks.base import ApplicationTask
from upaas_admin.apps.tasks.constants import *


@cache_page(2)  # TODO make it configurable?
@dajaxice_register
@login_required
def user_tasks(request):
    tasks = []
    running = 0
    # look for running or pending tasks and recently finished tasks
    for task in ApplicationTask.objects(
            Q(application__in=request.user.applications) & (
            Q(status__in=ACTIVE_TASK_STATUSES) |
            Q(date_finished__gte=datetime.now() - timedelta(seconds=180)))):

        #TODO make that 180 seconds configurable (?)

        if task.status == TaskStatus.pending:
            icon = ICON_PENDING
            running += 1
        elif task.status == TaskStatus.failed:
            icon = ICON_FAILED
        elif task.status == TaskStatus.successful:
            icon = ICON_SUCCESSFUL
        else:
            icon = ICON_STARTED
            running += 1

        date_finished = None
        if task.date_finished:
            date_finished = task.date_finished.isoformat()

        locked_since = None
        if task.locked_since:
            locked_since = task.locked_since.isoformat()

        tasks.append({'task_id': task.safe_id, 'title': task.title,
                      'date_created': task.date_created.isoformat(),
                      'date_finished': date_finished,
                      'locked_since': locked_since,
                      'status': task.status,
                      'pending': task.status == TaskStatus.pending,
                      'progress': task.progress, 'icon': icon,
                      'application': {'name': task.application.name,
                                      'id': task.application.safe_id}})
    return dumps({'tasks': tasks, 'running': running})
