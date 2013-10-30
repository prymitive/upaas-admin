# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import logging
from datetime import datetime, timedelta
from json import dumps

from mongoengine import Q

from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from dajaxice.decorators import dajaxice_register

from upaas_admin.apps.tasks.base import ApplicationTask
from upaas_admin.apps.applications.models import Application
from upaas_admin.apps.servers.constants import PortsNames
from upaas_admin.apps.tasks.constants import *
from upaas_admin.common.uwsgi import fetch_json_stats


def task_to_json(task, application, already_running):
    if task.status == TaskStatus.pending:
        icon = ICON_PENDING
        already_running += 1
    elif task.status == TaskStatus.failed:
        icon = ICON_FAILED
    elif task.status == TaskStatus.successful:
        icon = ICON_SUCCESSFUL
    else:
        icon = ICON_STARTED
        already_running += 1

    date_finished = None
    if task.date_finished:
        date_finished = task.date_finished.isoformat()

    locked_since = None
    if task.locked_since:
        locked_since = task.locked_since.isoformat()

    task_data = {
        'task_id': task.safe_id,
        'title': task.title,
        'date_created': task.date_created.isoformat(),
        'date_finished': date_finished,
        'locked_since': locked_since,
        'status': task.status,
        'pending': task.status == TaskStatus.pending,
        'failed': task.status == TaskStatus.failed,
        'progress': task.progress,
        'icon': icon,
        'application': {'name': application.name, 'id': application.safe_id},
        'subtasks': [],
    }

    return already_running, task_data


@login_required
@dajaxice_register
@cache_page(3)  # TODO make it configurable?
def stats(request, app_id):
    data = []
    app = Application.objects.filter(id=app_id, owner=request.user).first()
    if app.run_plan:
        for backend in app.run_plan.backends:
            ports_data = backend.application_ports(app)
            if ports_data and ports_data.ports.get(PortsNames.stats):
                s = fetch_json_stats(str(backend.ip),
                                     ports_data.ports[PortsNames.stats])
                if s:
                    data.append(
                        {'backend': {'name': backend.name,
                                     'ip': str(backend.ip)},
                         'stats': s})
    return dumps({'stats': data})


@cache_page(2)  # TODO make it configurable?
@dajaxice_register
@login_required
def user_tasks(request):
    tasks = []
    skip_vtasks = []
    running = 0
    # look for running or pending tasks and recently finished tasks
    for task in ApplicationTask.objects(
        Q(application__in=request.user.applications) & (
            Q(status__in=ACTIVE_TASK_STATUSES) |
            Q(date_finished__gte=datetime.now() - timedelta(seconds=300)))):
        #TODO make that 300 seconds configurable (?)
        #TODO optimize query, fetch all subtasks at once (?)

        if task.parent and task.parent.id in skip_vtasks:
            continue
        elif task.parent:
            running, data = task_to_json(task.parent, task.application,
                                         running)
            subtasks = ApplicationTask.objects(parent=task.parent)
            subtasks_data = []
            for subtask in subtasks:
                _, subdata = task_to_json(subtask, task.application, 0)
                subdata['progress'] = int(subdata['progress'] / len(subtasks))
                subtasks_data.append(subdata)
            data['subtasks'] = subtasks_data
            skip_vtasks.append(task.parent.id)
            tasks.append(data)
        else:
            running, data = task_to_json(task, task.application, running)
            tasks.append(data)

    return dumps({'tasks': tasks, 'running': running})


@dajaxice_register
@login_required
def task_messages(request, task_id, offset):
    messages = []
    progress = 0
    task = ApplicationTask.objects(
        id=task_id, application__in=request.user.applications).first()
    if task:
        progress = task.progress
        for msg in task.messages[int(offset):]:
            messages.append({
                'timestamp': msg.timestamp.isoformat(),
                'source': msg.source,
                'level': logging.getLevelName(msg.level),
                'message': msg.message,
            })

    return dumps({'messages': messages, 'progress': progress})
