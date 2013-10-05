# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import absolute_import

import os
import time

from celery import task, current_task, group
from celery.utils.log import get_task_logger
from celery.exceptions import Ignore
from celery.states import FAILURE

from upaas.config.main import load_main_config
from upaas.config.metadata import MetadataConfig
from upaas.builder.builder import Builder
from upaas.builder import exceptions
from upaas.config.base import ConfigurationError
from upaas import processes

from upaas_admin.apps.applications.models import Package, Application
from upaas_admin.apps.applications.exceptions import UnpackError
from upaas_admin.apps.servers.models import BackendServer
# FIXME mongoengine complains that User model is not registered without it
from upaas_admin.apps.users.models import User
from upaas_admin.apps.tasks.constants import STATE_PROGRESS

log = get_task_logger(__name__)


@task
def start_application(app_id):
    app = Application.objects(id=app_id).first()
    if not app or not app.run_plan or not app.run_plan.backends:
        start_application.update_state(state=FAILURE)
        raise Ignore()

    job = group([start_package.subtask((app.current_package.safe_id,),
                                       options={'queue': b.name})
                 for b in app.run_plan.backends])
    result = job.apply_async()
    while not result.ready():
        start_application.update_state(
            state=STATE_PROGRESS, meta={'progress': result.completed_count()})
        time.sleep(1)
        log.info(u"Waiting for subtasks")
    start_application.update_state(state=STATE_PROGRESS,
                                   meta={'progress': result.completed_count()})


@task
def stop_application(app_id):
    app = Application.objects(id=app_id).first()
    if not app or not app.run_plan or not app.run_plan.backends:
        stop_application.update_state(state=FAILURE)
        raise Ignore()

    for backend in app.run_plan.backends:
        log.info(u"Removing application ports from '%s'" % backend.name)
        backend.delete_application_ports(app)

    job = group([stop_package.subtask((app.current_package.safe_id,),
                                      options={'queue': b.name})
                 for b in app.run_plan.backends])
    result = job.apply_async()
    waited = 0
    max_wait = 60
    while not result.ready():
        stop_application.update_state(
            state=STATE_PROGRESS, meta={'progress': result.completed_count()})
        #FIXME proper handling for timeouts and exceptions
        if waited < max_wait:
            time.sleep(1)
            waited += 1
            log.info(u"Waiting for subtasks (%d)" % waited)
        else:
            log.error(u"Waited too long (%d times)" % waited)
            stop_application.update_state(state=FAILURE)
            app.run_plan.delete()
            raise Ignore()
    stop_application.update_state(state=STATE_PROGRESS,
                                  meta={'progress': result.completed_count()})

    app.run_plan.delete()


@task
def update_application(app_id):
    app = Application.objects(id=app_id).first()
    if not app or not app.run_plan or not app.run_plan.backends:
        update_application.update_state(state=FAILURE)
        raise Ignore()

    job = group([update_package.subtask((app.current_package.safe_id,),
                                        options={'queue': b.name})
                 for b in app.run_plan.backends])
    result = job.apply_async()
    while not result.ready():
        update_application.update_state(
            state=STATE_PROGRESS, meta={'progress': result.completed_count()})
        time.sleep(1)
        log.info(u"Waiting for subtasks")
    update_application.update_state(
        state=STATE_PROGRESS, meta={'progress': result.completed_count()})
