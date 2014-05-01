# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

from time import sleep
from datetime import datetime, timedelta
import os
import logging

from mongoengine import Q

from django.utils.translation import ugettext as _

from upaas_admin.apps.applications.models import ApplicationFlag
from upaas_admin.apps.scheduler.models import ApplicationRunPlan
from upaas_admin.apps.applications.constants import (
    NeedsRestartFlag, NeedsStoppingFlag, NeedsRemovingFlag)
from upaas_admin.apps.tasks.mule import FlagMuleCommand
from upaas_admin.common.uwsgi import fetch_json_stats
from upaas_admin.apps.applications.exceptions import UnpackError


log = logging.getLogger(__name__)


class Command(FlagMuleCommand):

    mule_name = _('Backend')

    def find_flag(self):
        flags = [NeedsStoppingFlag.name, NeedsRestartFlag.name,
                 NeedsRemovingFlag.name]
        remove_q = {
            'pending__ne': False,
            'name': NeedsRemovingFlag.name,
            'options__%s__ne' % self.backend.id: False,
        }
        other_q = {
            'pending__ne': False,
            'name__in': [NeedsStoppingFlag.name, NeedsRestartFlag.name],
            'application__in': ApplicationRunPlan.objects(
                backends__backend=self.backend).distinct('application'),
        }
        ApplicationFlag.objects(Q(**remove_q) | Q(**other_q)).order_by(
            '-date_created').update_one(
                set__pending=False,
                set__locked_since=datetime.now(),
                set__locked_by_backend=self.backend,
                set__locked_by_pid=self.pid)
        return ApplicationFlag.objects(name__in=flags,
                                       locked_by_backend=self.backend,
                                       locked_by_pid=self.pid,
                                       pending=False).first()

    def handle_task(self):
        task_handled = super(Command, self).handle_task()
        if task_handled:
            return task_handled
        for app in ApplicationRunPlan.objects(
                backends__backend=self.backend).distinct('application'):
            if app.flags.filter(name__in=[NeedsRemovingFlag.name,
                                          NeedsStoppingFlag.name]):
                continue
            if not self.is_application_running(app):
                log.info(_("Application {name} needs starting").format(
                    name=app.name))
                run_plan = ApplicationRunPlan.objects(application=app).first()
                if run_plan:
                    task = self.create_task(
                        app, _('Starting application instance'))
                    self.start_app(task, app, run_plan)
                    self.remove_logger()

    def handle_flag(self, flag):
        if flag.name == NeedsStoppingFlag.name:
            log.info(_("Application {name} needs stopping").format(
                name=flag.application.name))
            task = self.create_task(flag.application, flag.title,
                                    flag=flag.name)
            self.stop_app(task, flag.application)
        elif flag.name == NeedsRestartFlag.name:
            log.info(_("Application {name} needs restarting").format(
                name=flag.application.name))
            task = self.create_task(flag.application, flag.title,
                                    flag=flag.name)
            self.restart_app(task, flag.application)

    def is_application_running(self, application):
        # FIXME better check
        return os.path.exists(application.vassal_path)

    def start_app(self, task, application, run_plan):
        backend_conf = run_plan.backend_settings(self.backend)
        if backend_conf:
            if backend_conf.package.id != application.current_package.id:
                backend_conf = run_plan.replace_backend_settings(
                    backend_conf.backend, backend_conf,
                    package=application.current_package.id)
            log.info(_("Starting application {name} using package "
                       "{id}").format(name=application.name,
                                      id=backend_conf.package.safe_id))

            if not os.path.exists(backend_conf.package.package_path):
                try:
                    backend_conf.package.unpack()
                except UnpackError as e:
                    log.error(_("Unpacking failed: {e}").format(e=e))
                    raise Exception(_("Unpacking failed: {e}").format(e=e))
            else:
                log.warning(_("Package already exists: {path}").format(
                    path=backend_conf.package.package_path))
            task.update(set__progress=50)

            backend_conf.package.save_vassal_config(backend_conf)
            # TODO handle backend start task failure with rescue code

            self.wait_until(application, running=True)
            log.info(_("Application '{name}' started").format(
                name=application.name))
            application.remove_unpacked_packages(
                exclude=[application.current_package])
            self.mark_task_successful(task)
        else:
            log.error(_("Backend {backend} missing in run plan for "
                        "{name}").format(backend=self.backend.name,
                                         name=application.name))
            self.fail(task)

    def restart_app(self, task, application):
        backend_conf = application.run_plan.backend_settings(self.backend)
        if backend_conf:
            backend_conf.package.save_vassal_config(backend_conf)
            task.update(set__progress=30)
            self.wait_until_reloaded(application)
            log.info(_("Application '{name}' restarted").format(
                name=application.name))
            self.mark_task_successful(task)
        else:
            self.fail(task)

    def stop_app(self, task, application):
        if os.path.isfile(application.vassal_path):
            log.info(_("Removing vassal config file {path}").format(
                path=application.vassal_path))
            try:
                os.remove(application.vassal_path)
            except OSError as e:
                log.error(_("Can't remove vassal config file at '{path}': "
                            "{err}").format(path=application.vassal_path,
                                            err=e))
                self.fail(task)
        else:
            log.warning(_("Vassal config file not found at '{path}").format(
                path=application.vassal_path))
        task.update(set__progress=10)

        self.wait_until(application, running=False)
        task.update(set__progress=75)

        run_plan = application.run_plan
        if run_plan:
            run_plan.remove_backend_settings(self.backend)
            run_plan.reload()
            if not run_plan.backends:
                log.info(_("Removing application run plan"))
                run_plan.delete()
        else:
            log.warning(_("Missing run plan for {name}, already "
                          "stopped?").format(name=self.application.name))

        application.remove_unpacked_packages()
        log.info(_("Application '{name}' stopped").format(
            name=application.name))
        self.mark_task_successful(task)

    def wait_until_reloaded(self, application, timelimit=300):
        # FIXME track pid change
        sleep(5)
        return self.wait_until(application, running=True)

    def wait_until(self, application, running=True, timelimit=300):

        run_plan = self.backend.application_settings(application)
        if not run_plan:
            return False

        if running:
            action = _("start")
        else:
            action = _("stop")

        backend_conf = run_plan.backend_settings(self.backend)
        if backend_conf:
            ip = str(self.backend.ip)
            name = application.name
            # FIXME track pid change instead of initial sleep (?)
            sleep(3)
            timeout = datetime.now() + timedelta(seconds=timelimit)
            logged = False
            while datetime.now() <= timeout:
                s = fetch_json_stats(ip, backend_conf.stats)
                if running and s:
                    return True
                if not running and not s:
                    return True
                if logged:
                    log.debug(_("Waiting for {name} to {action}").format(
                        name=name, action=action))
                else:
                    log.info(_("Waiting for {name} to {action}").format(
                        name=name, action=action))
                    logged = True
                sleep(2)
            else:
                log.error(_("Timeout reached for {name}").format(name=name))

        return False
