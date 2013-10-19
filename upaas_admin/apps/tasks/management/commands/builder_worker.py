# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import logging
import time

from django.core.management.base import BaseCommand

from upaas_admin.apps.applications.tasks import BuildPackageTask
from upaas_admin.apps.tasks.registry import tasks_autodiscover


log = logging.getLogger(__name__)


tasks_autodiscover()


class Command(BaseCommand):

    help = 'Run builder worker'

    def handle(self, *args, **options):
        while True:
            try:
                BuildPackageTask.cleanup_local_tasks()
                task = BuildPackageTask.pop()
                if task:
                    log.info(u"Got task '%s' - %s" % (task.id,
                                                      task.__class__.__name__))
                    task.execute()
                else:
                    log.debug(u"No task popped, sleeping")
                    time.sleep(2)
            except KeyboardInterrupt:
                log.info(u"Got ctr+c, exiting")
                break
