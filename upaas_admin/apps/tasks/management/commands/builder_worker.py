# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import logging
import time

from django.core.management.base import BaseCommand

from upaas_admin.apps.applications.utasks import BuildPackageTask

log = logging.getLogger(__name__)


class Command(BaseCommand):

    help = 'Run builder worker'

    def handle(self, *args, **options):
        while True:
            try:
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
