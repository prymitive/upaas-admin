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

from upaas_admin.apps.applications.models import Application
from upaas_admin.apps.tasks.models import Task


@login_required
@dajaxice_register
def task_status(request, task_id):
    # fetch user application
    apps = Application.objects(owner=request.user)
    # filter tasks we can display
    task = Task.objects.filter(application__in=apps, task_id=task_id).first()
    if task:
        # if task is owned by user we can display its status
        result = AsyncResult(task_id)
        return dumps(dict(status=result.status, result=result.result))
    raise PermissionDenied
