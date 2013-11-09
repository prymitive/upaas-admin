# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from os import getuid
from sys import exit
import logging

from optparse import make_option

from django.core.management.base import BaseCommand
from django.conf import settings

from upaas.builder.builder import OSBuilder
from upaas.builder import exceptions
from upaas.distro import distro_image_filename
from upaas.storage.exceptions import StorageError


log = logging.getLogger("bootstrap_os_image")


class Command(BaseCommand):

    help = 'Generate base OS image'

    option_list = BaseCommand.option_list + (
        make_option('--force', action='store_true', dest='force',
                    default=False, help=u'Generate new OS image even if there '
                                        u'is valid one already generated'),)

    def handle(self, *args, **options):
        builder = OSBuilder(settings.UPAAS_CONFIG)
        if options['force'] or not builder.has_valid_os_image():
            if getuid() != 0:
                log.error(u"You must run this command as root user, aborting")
                exit(1)
            if builder.storage.exists(distro_image_filename()):
                log.info(u"Deleting current OS image")
                try:
                    builder.storage.delete(distro_image_filename())
                except StorageError:
                    log.error(u"Deletion failed")
                    exit(2)
            try:
                builder.bootstrap_os()
            except exceptions.OSBootstrapError:
                log.error(u"Bootstrap failed")
                exit(3)
            except StorageError:
                log.error(u"Upload failed")
                exit(4)
        else:
            log.info(u"Bootstrap not needed, skipping (use --force to run "
                     u"bootstrap anyway)")
