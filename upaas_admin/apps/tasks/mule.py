# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import logging
import signal
from os import getpid
from datetime import datetime, timedelta
from time import sleep
from socket import gethostname
from threading import Thread
from multiprocessing import cpu_count

from IPy import IP

from optparse import make_option

from mongoengine import Q
from mongoengine.errors import NotUniqueError

from django.core.management.base import NoArgsCommand
from django.utils.translation import ugettext as _

from upaas.inet import local_ipv4_addresses
from upaas.processes import is_pid_running
from upaas.utils import backend_total_memory

from upaas_admin.apps.servers.models import BackendServer
from upaas_admin.apps.tasks.models import MongoLogHandler, Task
from upaas_admin.apps.tasks.constants import TaskStatus
from upaas_admin.apps.applications.constants import SINGLE_SHOT_FLAGS
from upaas_admin.apps.applications.models import ApplicationFlag, FlagLock


log = logging.getLogger(__name__)


class MuleTaskFailed(Exception):
    """
    Raised inside handle_flag() if task failed.
    """
    pass


class MuleBackendHelper(object):

    def __init__(self, name):
        self.exiting = False
        self.name = name
        self.interval = 0
        self.backend = self.register_backend()

    def pinger(self):
        key = 'set__worker_ping__%s' % self.name
        while not self.exiting:
            self.backend.update(**{key: datetime.now()})
            sleep(self.interval)

    def start_pinger(self, interval=60):
        self.interval = interval
        t1 = Thread(target=self.pinger)
        t1.start()

    def stop_pinger(self):
        self.exiting = True

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
            log.error(_("No IP address found for local backend!"))
            return

        if backend:
            if backend.autodetect:
                self.update_backend(backend)
        else:
            log.info(_("Local backend not found, registering as '{name}' "
                       "with IP {ip}").format(name=name, ip=local_ip))
            backend = BackendServer(name=name, ip=local_ip, is_enabled=False,
                                    cpu_cores=cpu_count(),
                                    memory_mb=backend_total_memory())
            backend.save()

        return backend

    def update_backend(self, backend):
        if backend.ip == IP('127.0.0.1'):
            # allow using localhost as backend IP, don't auto update
            # it in such case
            return

        updates = {}

        local_ips = local_ipv4_addresses()
        if backend.ip not in [IP(ip) for ip in local_ips]:
            local_ip = local_ips[0]
            log.info(_("Updating IP for {name} from {oldip} to "
                       "{newip}").format(name=backend.name, oldip=backend.ip,
                                         newip=local_ip))
            updates['set__ip'] = local_ip

        cpus = cpu_count()
        if backend.cpu_cores != cpus:
            log.info(_("Updating cpu cores for {name} from {oldcpus} to "
                       "{cpus}").format(name=backend.name,
                                        oldcpus=backend.cpu_cores or 0,
                                        cpus=cpus))
            updates['set__cpu_cores'] = cpus

        mem = backend_total_memory()
        if mem:
            # convert to MB
            mem = mem / 1024 / 1024
            if backend.memory_mb != mem:
                log.info(_(
                    "Updating memory size for {name} from {oldmem}MB to "
                    "{mem}MB").format(name=backend.name,
                                      oldmem=backend.memory_mb or 0,
                                      mem=mem))
                updates['set__memory_mb'] = mem
        else:
            log.error(_("Can't find local backend physical memory size, "
                        "is /proc mounted ?"))

        if updates:
            backend.update(**updates)
            backend.reload()


class MuleTaskHelper(object):

    def __init__(self, name):
        self.name = name
        self.last_clean = {}

    def clean(self, backend):
        self.clean_failed_locks(backend)
        self.clean_failed_tasks(backend)
        self.clean_failed_remote_tasks(backend)
        self.clean_failed_remote_locks(backend)
        self.clean_orphaned_locks()

    def can_clean(self, name):
        if self.last_clean.get(name) is None:
            return True
        if self.last_clean.get(name, 0) < (
                datetime.now() - timedelta(seconds=60)):
            return True
        return False

    def reset_pending_state(self, lock):
        if lock.flag in SINGLE_SHOT_FLAGS:
            ApplicationFlag.objects(
                application=lock.application, name=lock.flag,
                pending=False).update_one(set__pending=True)
        else:
            ApplicationFlag.objects(
                application=lock.application, name=lock.flag,
                pending_backends__ne=lock.backend).update_one(
                    add_to_set__pending_backends=lock.backend)

    def clean_failed_tasks(self, backend):
        name = 'local_tasks'
        if not self.can_clean(name):
            return
        for task in Task.objects(backend=backend,
                                 status=TaskStatus.running):
            if not is_pid_running(task.pid):
                log.warning(_(
                    "Found failed task, marking as failed (id: {id}, app: "
                    "{name})").format(id=task.safe_id,
                                      name=task.application.name))
                task.update(set__status=TaskStatus.failed,
                            set__date_finished=datetime.now())
        self.last_clean[name] = datetime.now()

    def clean_failed_locks(self, backend):
        name = 'local_locks'
        if not self.can_clean(name):
            return
        for lock in FlagLock.objects(backend=backend):
            if not is_pid_running(lock.pid):
                log.warning(_("Found stale lock, removing (app: {name}, pid: "
                              "{pid})").format(name=lock.application.name,
                                               pid=lock.pid))
                self.reset_pending_state(lock)
                lock.delete()
        self.last_clean[name] = datetime.now()

    def clean_failed_remote_tasks(self, local_backend):
        name = 'remote_tasks'
        if not self.can_clean(name):
            return
        # look for tasks locked at backends that did not ack itself to the
        # database for at least 600 seconds
        timestamp = datetime.now() - timedelta(seconds=600)
        backends = BackendServer.objects(**{
            'id__ne': local_backend.id,
            'worker_ping__%s__lte' % self.name: timestamp
        })
        if backends:
            log.debug(_("{len} non responsive backends: {names}").format(
                len=len(backends), names=[b.name for b in backends]))
            for task in Task.objects(locked_by_backend__in=backends,
                                     locked_since__lte=timestamp):
                log.warning(_("Task '{name}' with id {tid} is locked on non "
                              "backend {backend}, but it didn't send any "
                              "pings for 10 minutes, marking as "
                              "failed").format(
                    name=task.title, tid=task.safe_id,
                    backend=task.locked_by_backend))
                task.update(set__status=TaskStatus.failed,
                            set__date_finished=datetime.now())
        self.last_clean[name] = datetime.now()

    def clean_failed_remote_locks(self, local_backend):
        name = 'remote_tasks'
        if not self.can_clean(name):
            return
        # look for tasks locked at backends that did not ack itself to the
        # database for at least 600 seconds
        timestamp = datetime.now() - timedelta(seconds=600)
        backends = BackendServer.objects(**{
            'id__ne': local_backend.id,
            'worker_ping__%s__lte' % self.name: timestamp
        })
        if backends:
            log.debug(_("{len} non responsive backends: {names}").format(
                len=len(backends), names=[b.name for b in backends]))
            for lock in FlagLock.objects(backend__in=backends,
                                         date_created__lte=timestamp):
                log.warning(_("Found old lock on  backend {backend}, but it "
                              "didn't send any pings for 10 minutes, "
                              "removing").format(backend=lock.backend))
                self.reset_pending_state(lock)
                lock.delete()
        self.last_clean[name] = datetime.now()

    def clean_orphaned_locks(self):
        name = 'orphaned_locks'
        if not self.can_clean(name):
            return
        timestamp = datetime.now() - timedelta(seconds=60)
        for lock in FlagLock.objects(
                backend__exists=False, flag__in=SINGLE_SHOT_FLAGS,
                date_created__lte=timestamp):
            if len(Task.objects(
                Q(application=lock.application, flag=lock.flag) & (
                    Q(status=TaskStatus.running) |
                    Q(date_finished__gte=(
                        datetime.now() - timedelta(seconds=30)))))) == 0:
                log.warning(_("Found stale lock, removing (app: "
                              "{name})").format(name=lock.application.name))
                self.reset_pending_state(lock)
                lock.delete()
        self.last_clean[name] = datetime.now()


class MuleCommand(NoArgsCommand):

    mule_name = _('Mule')
    mule_flags = []

    option_list = NoArgsCommand.option_list + (
        make_option('--task-limit', dest='task_limit', type=int, default=0,
                    help=_('Exit after processing given number of tasks '
                           '(default is no limit)')),
        make_option('--ping-disabled', action="store_true",
                    dest='ping_disabled', default=False,
                    help=_('Disable health check pings')),
        make_option('--ping-interval', dest='ping_interval', type=int,
                    default=60, help=_('Health check ping interval (default is'
                                       ' 60 seconds)')),
    )

    def __init__(self, *args, **kwargs):
        super(MuleCommand, self).__init__(*args, **kwargs)

        self.backend_helper = MuleBackendHelper(
            self.mule_name.replace(' ', ''))
        self.backend = self.backend_helper.backend

        self.task_helper = MuleTaskHelper(self.mule_name.replace(' ', ''))

        self.is_exiting = False
        self.tasks_done = 0
        self.task_limit = 0
        self.cleanup()
        self.pid = getpid()
        self.log_handler = None
        self.log_handlers_level = {}
        # FIXME capture all logs and prefix with self.logger

    def cleanup(self):
        self.app_name = _('N/A')

    def add_logger(self, task):
        self.log_handler = MongoLogHandler(task)
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            self.log_handlers_level[handler] = handler.level
            handler.level = logging.ERROR
        root_logger.addHandler(self.log_handler)

    def remove_logger(self):
        if self.log_handler:
            self.log_handler.flush()
        if self.log_handlers_level:
            root_logger = logging.getLogger()
            for handler in root_logger.handlers:
                level = self.log_handlers_level.get(handler)
                if level is not None:
                    handler.level = level
        if self.log_handler:
            root_logger.removeHandler(self.log_handler)

    def mark_exiting(self, *args):
        log.info(_("Shutting down, waiting for current task to finish"))
        self.is_exiting = True

    def create_task(self, application, title, flag=None):
        task = Task(backend=self.backend, pid=self.pid, title=title,
                    application=application)
        if flag:
            task.flag = flag
        task.save()
        self.add_logger(task)
        return task

    def fail_task(self, task):
        self.remove_logger()
        self.cleanup()
        task.update(set__status=TaskStatus.failed,
                    set__date_finished=datetime.now())
        log.error(_("Task failed for {name} [{id}]").format(
            name=task.application.name, id=task.application.safe_id))
        raise MuleTaskFailed

    def mark_task_successful(self, task):
        task.update(set__status=TaskStatus.successful, set__progress=100,
                    set__date_finished=datetime.now())

    def task_completed(self):
        self.tasks_done += 1
        log.info(_("Task completed, [done: {tasks_done}, limit: "
                   "{task_limit}]").format(tasks_done=self.tasks_done,
                                           task_limit=self.task_limit))

    def handle_noargs(self, **options):
        for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP,
                    signal.SIGQUIT]:
            signal.signal(sig, self.mark_exiting)

        if not options['ping_disabled']:
            self.backend_helper.start_pinger(interval=options['ping_interval'])

        self.task_limit = options['task_limit']
        log.info(_("{name} ready, waiting for tasks (limit: "
                   "{task_limit})").format(name=self.mule_name,
                                           task_limit=self.task_limit))
        while True:
            if self.task_limit and self.tasks_done >= self.task_limit:
                log.info(_('Task limit reached {task_limit}, exiting').format(
                    task_limit=self.task_limit))
                self.is_exiting = True

            if self.is_exiting:
                self.backend_helper.stop_pinger()
                return

            self.task_helper.clean(self.backend)
            self.handle_task()
            sleep(1)

    def handle_task(self):
        flag = self.find_flag()
        if flag:
            failed = False
            try:
                self.handle_flag(flag)
            except MuleTaskFailed:
                failed = True
            finally:
                self.unlock_flag(flag)
                self.remove_logger()
                self.task_completed()
            if failed:
                return True

            if flag.name in SINGLE_SHOT_FLAGS:
                ApplicationFlag.objects(application=flag.application,
                                        name=flag.name,
                                        pending=False).delete()
            else:
                flag.update(pull__pending_backends=self.backend)
                ApplicationFlag.objects(application=flag.application,
                                        name=flag.name,
                                        pending_backends__size=0).delete()
            self.cleanup()
            return True

        return False

    def handle_flag(self, flag):
        raise NotImplementedError

    def fail_flag(self, flag, task):
        flag.delete()
        self.fail_task(task)

    def flag_filter(self):
        single_shot_flags = []
        multi_show_flags = []
        for flag in self.mule_flags:
            if flag in SINGLE_SHOT_FLAGS:
                single_shot_flags.append(flag)
            else:
                multi_show_flags.append(flag)
        return ApplicationFlag.objects(
            (
                Q(pending__ne=False) &
                Q(name__in=single_shot_flags) &
                Q(application__nin=FlagLock.objects(
                    flag__in=single_shot_flags).distinct('application'))
            ) | (
                Q(pending_backends=self.backend) &
                Q(name__in=multi_show_flags) &
                Q(application__nin=FlagLock.objects(
                    flag__in=multi_show_flags,
                    backend=self.backend).distinct('application'))
            )
        )

    def find_flag(self):
        if not self.mule_flags:
            raise RuntimeError(_('No flags set for mule'))
        flag = self.flag_filter().first()
        if flag:
            kwargs = {}
            if flag.name in SINGLE_SHOT_FLAGS:
                flag.update(set__pending=False)
            else:
                kwargs['backend'] = self.backend

            lock = FlagLock(application=flag.application, flag=flag.name,
                            pid=self.pid, **kwargs)
            try:
                lock.save()
            except NotUniqueError:
                return

            return flag

    def unlock_flag(self, flag):
        if flag.name in SINGLE_SHOT_FLAGS:
            lock = FlagLock.objects(application=flag.application,
                                    flag=flag.name,
                                    backend__exists=False).first()
        else:
            lock = FlagLock.objects(application=flag.application,
                                    flag=flag.name,
                                    backend=self.backend).first()
        if lock:
            lock.delete()
