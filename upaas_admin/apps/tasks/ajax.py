# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from json import dumps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.decorators.cache import cache_page

from dajaxice.decorators import dajaxice_register

from celery.result import AsyncResult
from celery.states import STARTED, PENDING

from upaas_admin.apps.tasks.models import Task
from upaas_admin.apps.tasks.constants import *


@login_required
@dajaxice_register
def task_status(request, task_id):
    task = Task.objects.filter(task_id=task_id).first()
    if task:
        if not task.application or task.application.owner == request.user:
            result = AsyncResult(task_id)
            return dumps(dict(status=result.status, result=result.result))
        raise PermissionDenied
    return dumps({})


@login_required
@dajaxice_register
@cache_page(2)  # TODO make it configurable?
def user_tasks(request):
    tasks = []
    running = 0
    for task in Task.objects(user=request.user):
        result = AsyncResult(task.task_id)
        if result.status in [PENDING, STARTED, STATE_PROGRESS]:
            if result.status == PENDING:
                icon = ICON_PENDING
            else:
                icon = ICON_STARTED

            running += 1
            progress = -1
            if result.info:
                progress = result.info.get('progress', -1)
            tasks.append({'task_id': task.task_id, 'title': task.title,
                          'date_created': task.date_created.isoformat(),
                          'status': result.status,
                          'progress': progress, 'icon': icon,
                          'application': {'name': task.application.name,
                                          'id': task.application.safe_id}})
    return dumps({'tasks': tasks, 'running': running})
