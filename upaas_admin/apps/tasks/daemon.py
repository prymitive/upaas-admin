# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import os
import sys
import logging
import signal
import time
import multiprocessing

from optparse import make_option

from django.core.management.base import BaseCommand

from upaas_admin.apps.tasks.registry import tasks_autodiscover


tasks_autodiscover()


log = logging.getLogger(__name__)


def worker_init():
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    log.info(u"New worker started with pid %d" % os.getpid())


def execute_task(task):
    pid = os.getpid()
    log.info(u"Pid %d taking over task '%s' with id '%s'" % (
        pid, task.__class__.__name__, task.safe_id))
    task.locked_by_pid = pid
    task.save()
    task.execute()


class DaemonCommand(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--workers', dest='workers', type=int, default=2,
                    help=u'Number of workers to spawn'),
    )

    task_class = None

    def __init__(self, *args, **kwargs):
        super(DaemonCommand, self).__init__(*args, **kwargs)
        self.pool = None
        self.is_exiting = False

    def worker_exit_handler(self, *args):
        log.info(u"Going to shutdown, waiting for worker(s) to terminate")
        self.is_exiting = True
        self.pool.close()
        self.pool.join()

    def pop_task(self, **kwargs):
        return self.task_class.pop(**kwargs)

    def handle(self, *args, **options):
        if self.task_class is None:
            log.error(u"Internal error: task class not set for worker daemon!")
            sys.exit(1)

        signal.signal(signal.SIGINT, self.worker_exit_handler)

        workers_count = options['workers']
        log.info(u"Started master process with pid %d, running %d worker"
                 u"(s)" % (os.getpid(), workers_count))
        self.pool = multiprocessing.Pool(workers_count, worker_init)

        results = []

        while True:
            if self.is_exiting:
                break
            self.task_class.cleanup_local_tasks()
            self.task_class.cleanup_remote_tasks()
            if len(results) < workers_count:
                task = self.pop_task()
                if task:
                    log.info(u"Got task '%s' - %s" % (task.id,
                                                      task.__class__.__name__))
                    result = self.pool.apply_async(execute_task, [task])
                    results.append(result)
                    time.sleep(1)
                else:
                    log.debug(u"No task popped, sleeping")
                    time.sleep(2)
            else:
                completed = []
                for r in results:
                    if r.ready():
                        completed.append(r)
                for r in completed:
                    results.remove(r)
                log.debug(u"%d out of %d worker(s) running" % (len(results),
                                                               workers_count))
                time.sleep(3)

        self.pool.close()
        self.pool.join()
