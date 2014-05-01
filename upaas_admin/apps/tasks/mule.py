# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import logging
import signal
from os import getpid
from datetime import datetime
from time import sleep
from socket import gethostname

from IPy import IP

from optparse import make_option

from django.core.management.base import NoArgsCommand
from django.utils.translation import ugettext as _

from upaas.inet import local_ipv4_addresses
from upaas.processes import is_pid_running

from upaas_admin.apps.servers.models import BackendServer
from upaas_admin.apps.tasks.models import MongoLogHandler, Task
from upaas_admin.apps.tasks.constants import TaskStatus
from upaas_admin.apps.applications.models import ApplicationFlag


log = logging.getLogger(__name__)


class MuleTaskFailed(Exception):
    """
    Raised inside handle_flag() if task failed.
    """
    pass


class BaseMuleCommand(NoArgsCommand):

    mule_name = _('Mule')

    option_list = NoArgsCommand.option_list + (
        make_option('--task-limit', dest='task_limit', type=int, default=0,
                    help=_('Exit after processing given number of tasks '
                           '(default is no limit)')),
    )

    def __init__(self, *args, **kwargs):
        super(BaseMuleCommand, self).__init__(*args, **kwargs)
        self.is_exiting = False
        self.tasks_done = 0
        self.cleanup()
        self.pid = getpid()
        self.register_backend()
        self.log_handler = None
        self.log_handlers_level = {}
        # FIXME capture all logs and prefix with self.logger

    def cleanup(self):
        self.app_name = _('N/A')

    def clean_failed_tasks(self):
        for task in Task.objects(backend=self.backend,
                                 status=TaskStatus.running):
            if not is_pid_running(task.pid):
                log.warning(_(
                    "Found failed task, marking as failed (id: {id}, app: "
                    "{name})").format(id=task.safe_id,
                                      name=task.application.name))
                task.update(set__status=TaskStatus.failed,
                            set__date_finished=datetime.now())

    def add_logger(self, task):
        self.log_handler = MongoLogHandler(task)
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            self.log_handlers_level[handler] = handler.level
            handler.level = logging.ERROR
        root_logger.addHandler(self.log_handler)

    def remove_logger(self):
        self.log_handler.flush()
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            level = self.log_handlers_level.get(handler)
            if level is not None:
                handler.level = level
        root_logger.removeHandler(self.log_handler)

    def mark_exiting(self, *args):
        log.info(_("Shutting down, waiting for current task to finish"))
        self.is_exiting = True

    def fail(self, task):
        self.remove_logger()
        self.cleanup()
        task.update(set__status=TaskStatus.failed,
                    set__date_finished=datetime.now())
        log.error(_("Task failed for {name} [{id}]").format(
            name=task.application.name, id=task.application.safe_id))
        raise MuleTaskFailed

    def create_task(self, application, title, flag=None):
        task = Task(backend=self.backend, pid=self.pid, title=title,
                    application=application)
        if flag:
            task.flag = flag
        task.save()
        self.add_logger(task)
        return task

    def mark_task_successful(self, task):
        task.update(set__status=TaskStatus.successful, set__progress=100,
                    set__date_finished=datetime.now())

    def register_backend(self):
        name = gethostname()
        local_ip = None

        backend = BackendServer.objects(name=name).first()
        if not backend:
            for local_ip in local_ipv4_addresses():
                backend = BackendServer.objects(ip=local_ip).first()
                if backend:
                    break

        if not backend and not local_ip:
            log.error("No IP address found for local backend!")
            return

        if backend:
            local_ips = local_ipv4_addresses()
            if backend.ip not in [IP(ip) for ip in local_ips]:
                local_ip = local_ips[0]
                log.info("Updating IP for '%s' from '%s' to '%s'" % (
                    name, backend.ip, local_ip))
                backend.ip = IP(local_ip)
                backend.save()
        else:
            log.info(_("Local backend not found, registering as '{name}' "
                       "with IP {ip}").format(name=name, ip=local_ip))
            backend = BackendServer(name=name, ip=local_ip, is_enabled=False)
            backend.save()

        self.backend = backend

    def handle_noargs(self, **options):
        for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP,
                    signal.SIGQUIT]:
            signal.signal(sig, self.mark_exiting)

        task_limit = options['task_limit']
        log.info(_("{name} ready, waiting for tasks (limit: "
                   "{task_limit})").format(name=self.mule_name,
                                           task_limit=task_limit))
        while True:
            if task_limit and self.tasks_done >= task_limit:
                log.info(_('Task limit reached {task_limit}, exiting').format(
                    task_limit=task_limit))
                self.is_exiting = True

            if self.is_exiting:
                return

            if self.handle_task():
                self.tasks_done += 1
                log.info(_("Task completed, [done: {tasks_done}, limit: "
                           "{task_limit}]").format(tasks_done=self.tasks_done,
                                                   task_limit=task_limit))
            else:
                self.clean_failed_tasks()
                sleep(2)


class FlagMuleCommand(BaseMuleCommand):

    mule_flags = []

    def fail_flag(self, flag, task):
        flag.delete()
        self.fail(task)

    def handle_task(self):
        flag = self.find_flag()
        if flag:
            if flag.locked_since:
                if flag.locked_by_pid != self.pid:
                    if not is_pid_running(flag.locked_by_pid):
                        log.warning(_("Found flag locked by non-existing "
                                      "PID {pid}").format(
                            pid=flag.locked_by_pid))
                        flag_task = Task.objects(
                            pid=flag.locked_by_pid,
                            backend=flag.locked_by_backend,
                            status=TaskStatus.running).first()
                        if flag_task:
                            flag_task.update(
                                set__status=TaskStatus.failed,
                                set__date_finished=datetime.now())
                        self.unlock_flag(flag)
                        return False

            try:
                self.handle_flag(flag)
            except MuleTaskFailed:
                return True
            finally:
                self.remove_logger()

            flag.reload()
            if not flag.pending:
                flag.delete()
            self.cleanup()
            return True

        return False

    def handle_flag(self, flag):
        raise NotImplementedError

    def flag_filter(self):
        return {}

    def find_flag(self):
        if not self.mule_flags:
            raise RuntimeError(_('No flags set for mule'))

        ApplicationFlag.objects(
            pending__ne=False,
            name__in=self.mule_flags,
            **self.flag_filter()).order_by(
                '-date_created').update_one(
                    set__pending=False,
                    set__locked_since=datetime.now(),
                    set__locked_by_backend=self.backend,
                    set__locked_by_pid=self.pid)
        return ApplicationFlag.objects(name__in=self.mule_flags,
                                       locked_by_backend=self.backend,
                                       pending=False).first()

    def unlock_flag(self, flag):
        flag.update(set__pending=True,
                    unset__locked_since=True,
                    unset__locked_by_backend=True,
                    unset__locked_by_pid=True)
