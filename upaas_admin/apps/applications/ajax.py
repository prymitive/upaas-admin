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
from upaas_admin.apps.tasks.constants import *
from upaas_admin.common.uwsgi import fetch_json_stats


def task_to_json(task, application, already_running):
    if task.is_active:
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
        'is_pending': task.is_pending,
        'is_active': task.is_active,
        'is_successful': task.is_successful,
        'is_failed': task.is_failed,
        'is_running': task.is_running,
        'is_finished': task.is_finished,
        'progress': task.progress,
        'icon': task.icon_class,
        'application': {'name': application.name, 'id': application.safe_id},
        'subtasks': [],
    }

    return already_running, task_data


def tasks_updates(user):
    tasks = []
    skip_vtasks = []
    running = 0

    # look for running or pending tasks and recently finished tasks
    for task in ApplicationTask.objects(
        Q(application__in=user.applications) & (
            Q(status__in=ACTIVE_TASK_STATUSES) |
            Q(date_finished__gte=datetime.now() - timedelta(seconds=300)))):
        #TODO make that 300 seconds configurable (?)
        #TODO optimize query, fetch all subtasks at once (?)

        if task.parent and task.parent.id in skip_vtasks:
            continue
        elif task.parent:
            running, data = task_to_json(task.parent, task.application,
                                         running)
            subtasks = task.parent.subtasks
            subtasks_count = len(subtasks)
            subtasks_data = []
            for subtask in subtasks:
                _, subdata = task_to_json(subtask, task.application, 0)
                subdata['progress'] = int(subdata['progress'] / subtasks_count)
                subtasks_data.append(subdata)
            data['subtasks'] = subtasks_data
            skip_vtasks.append(task.parent.id)
            tasks.append(data)
        else:
            running, data = task_to_json(task, task.application, running)
            tasks.append(data)

    return {'list': tasks, 'running': running}


@login_required
@dajaxice_register
@cache_page(3)  # TODO make it configurable?
def instances(request, app_id):
    stats = []
    app = Application.objects.filter(id=app_id, owner=request.user).first()
    run_plan = app.run_plan
    if run_plan:
        for backend_conf in app.run_plan.backends:
            backend_data = {
                'name': backend_conf.backend.name,
                'ip': str(backend_conf.backend.ip),
                'limits': {
                    'workers_min': backend_conf.workers_min,
                    'workers_max': backend_conf.workers_max,
                    'memory_per_worker': run_plan.memory_per_worker,
                    'memory_per_worker_bytes': run_plan.memory_per_worker *
                    1024 * 1024,
                    'backend_memory': run_plan.memory_per_worker *
                    backend_conf.workers_max,
                    'backend_memory_bytes': run_plan.memory_per_worker *
                    backend_conf.workers_max * 1024 * 1024,
                }}
            s = fetch_json_stats(str(backend_conf.backend.ip),
                                 backend_conf.stats)
            stats.append({'backend': backend_data, 'stats': s})
    return dumps({'stats': stats})


@cache_page(2)  # TODO make it configurable?
@dajaxice_register
@login_required
def apps_updates(request):
    all_apps = []
    running_apps = []
    for app in request.user.applications:
        active_tasks = []
        for task in app.active_tasks:
            _, task_data = task_to_json(task, app, 0)
            active_tasks.append(task_data)
        app_data = {
            'id': app.safe_id,
            'name': app.name,
            'packages': len(app.packages),
            'is_running': app.run_plan is not None,
            'instances': len(app.run_plan.backends) if app.run_plan else 0,
            'active_tasks': active_tasks
        }
        all_apps.append(app_data)
        if app.run_plan:
            running_apps.append(app_data)
    apps = {'list': all_apps, 'running': running_apps}
    return dumps({'apps': apps, 'tasks': tasks_updates(request.user)})


@dajaxice_register
@login_required
def task_messages(request, task_id, offset):
    ret = {'is_pending': None, 'is_running': None, 'is_finished': None,
           'is_failed': None, 'is_successful': None, 'messages': [],
           'progress': 0}
    task = ApplicationTask.objects(
        id=task_id, application__in=request.user.applications).first()
    if task:
        ret['progress'] = task.progress
        ret['is_pending'] = task.is_pending
        ret['is_running'] = task.is_running
        ret['is_finished'] = task.is_finished
        ret['is_failed'] = task.is_failed
        ret['is_successful'] = task.is_successful
        messages = []
        for msg in task.messages[int(offset):]:
            messages.append({
                'timestamp': msg.timestamp.isoformat(),
                'source': msg.source,
                'level': logging.getLevelName(msg.level),
                'message': msg.message,
            })
        ret['messages'] = messages

    return dumps(ret)
