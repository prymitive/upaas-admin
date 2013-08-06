# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from json import dumps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from dajaxice.decorators import dajaxice_register

from celery.result import AsyncResult

from upaas_admin.apps.tasks.models import Task


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
