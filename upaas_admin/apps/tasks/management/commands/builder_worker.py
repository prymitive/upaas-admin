# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import logging
import time

from django.core.management.base import BaseCommand

from upaas_admin.apps.tasks.constants import BUILDER_QUEUE
from upaas_admin.apps.tasks.models import Task

log = logging.getLogger(__name__)


class Command(BaseCommand):

    help = 'Run builder worker'

    def handle(self, *args, **options):
        while True:
            try:
                task = Task.pop([BUILDER_QUEUE])
                if task:
                    log.info(u"Got task '%s' - '%s.%s'" % (task.id,
                                                           task.task_module,
                                                           task.task_class))
                    task.execute()
                else:
                    log.debug(u"No task popped, sleeping")
                    time.sleep(2)
            except KeyboardInterrupt:
                log.info(u"Got ctr+c, exiting")
                break
