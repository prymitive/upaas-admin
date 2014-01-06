# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import os
import sys
import logging
import signal
import time
import multiprocessing
from socket import gethostname
from datetime import datetime

from IPy import IP

from optparse import make_option

from django.core.management.base import BaseCommand

from upaas.inet import local_ipv4_addresses

from upaas_admin.apps.tasks.registry import tasks_autodiscover
from upaas_admin.apps.servers.models import BackendServer


tasks_autodiscover()


log = logging.getLogger(__name__)


def worker_init():
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    log.info("New worker started with pid %d" % os.getpid())


def execute_task(task):
    pid = os.getpid()
    log.info("Pid %d taking over task '%s' with id '%s'" % (
        pid, task.__class__.__name__, task.safe_id))
    task.locked_by_pid = pid
    task.save()
    task.execute()


class DaemonCommand(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--workers', dest='workers', type=int, default=2,
                    help='Number of workers to spawn'),
        make_option('--task-limit', dest='task_limit', type=int, default=0,
                    help='Exit after processing given number of tasks '
                         '(default is no limit)'),
    )

    task_class = None

    def __init__(self, *args, **kwargs):
        super(DaemonCommand, self).__init__(*args, **kwargs)
        self.pool = None
        self.is_exiting = False
        self.tasks_done = 0

    def worker_exit_handler(self, *args):
        log.info("Going to shutdown, waiting for worker(s) to terminate")
        self.is_exiting = True
        self.pool.close()
        self.pool.join()

    def pop_task(self, **kwargs):
        return self.task_class.pop(self.backend, **kwargs)

    def register_backend(self):
        name = gethostname()
        local_ip = None

        backend = BackendServer.objects(name=name).first()
        if not backend:
            for local_ip in local_ipv4_addresses():
                log.debug("Looking for backend with IP '%s'" % local_ip)
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
            log.info("Local backend not found, registering as '%s' with IP "
                     "'%s'" % (name, local_ip))
            backend = BackendServer(name=name, ip=local_ip, is_enabled=False)
            backend.save()

        self.backend = backend

    def ping(self):
        args = {}
        key = 'set__worker_ping__%s' % self.task_class.__name__
        args[key] = datetime.now()
        BackendServer.objects(id=self.backend.id).update_one(**args)

    def handle(self, *args, **options):
        if self.task_class is None:
            log.error("Internal error: task class not set for worker daemon!")
            sys.exit(1)

        signal.signal(signal.SIGINT, self.worker_exit_handler)

        self.register_backend()

        workers_count = options['workers']
        task_limit = options['task_limit']
        log.info("Started master process with pid %d, running %d worker (s), "
                 "task class: %s, task limit %d" % (
                     os.getpid(), workers_count, self.task_class.__name__,
                     task_limit))
        self.pool = multiprocessing.Pool(workers_count, worker_init)

        results = []

        while True:
            if self.is_exiting:
                break
            self.ping()
            self.task_class.cleanup_local_tasks(self.backend)
            self.task_class.cleanup_remote_tasks(self.backend)
            if len(results) < workers_count:
                task = self.pop_task()
                if task:
                    self.tasks_done += 1
                    log.info("Got task '%s' - %s" % (task.id,
                                                     task.__class__.__name__))
                    result = self.pool.apply_async(execute_task, [task])
                    results.append(result)
                    if task_limit and self.tasks_done >= task_limit:
                        log.info("Task limit reached (%d), exiting",
                                 task_limit)
                        self.is_exiting = True
                    else:
                        time.sleep(1)
                else:
                    log.debug("No task popped, sleeping (done: %d, limit: "
                              "%d)" % (self.tasks_done, task_limit))
                    time.sleep(2)
            else:
                completed = []
                for r in results:
                    if r.ready():
                        completed.append(r)
                for r in completed:
                    results.remove(r)
                log.debug("%d out of %d worker(s) running" % (len(results),
                                                              workers_count))
                time.sleep(3)

        self.pool.close()
        self.pool.join()
