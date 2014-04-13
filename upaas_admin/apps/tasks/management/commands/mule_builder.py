# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import logging
from os import getpid
from signal import signal, SIGINT
from datetime import datetime
from time import sleep
from socket import gethostname

from IPy import IP

from django.core.management.base import NoArgsCommand

from upaas.inet import local_ipv4_addresses

from upaas_admin.apps.applications.models import Application, ApplicationFlag
from upaas_admin.apps.servers.models import BackendServer


log = logging.getLogger(__name__)


class Command(NoArgsCommand):

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.is_exiting = False
        self.pid = getpid()
        self.register_backend()

    def mark_exiting(self, *args):
        print('Exiting')
        self.is_exiting = True

    def handle_noargs(self, **options):
        signal(SIGINT, self.mark_exiting)

        while True:
            if self.is_exiting:
                return
            print('Looking for app to build')
            flag = self.find_flag()
            print('GOT: %s' % flag)
            if flag:
                print('Building')
            else:
                sleep(2)

    def find_flag(self):
        """
        Find application that needs new package, return None if nothing to do.
        """
        ret = ApplicationFlag.objects(
            pending__ne=False,
            name=ApplicationFlag.FlagName.needs_building).update_one(
                set__pending=False,
                set__locked_since=datetime.now(),
                set__locked_by_backend=self.backend,
                set__locked_by_pid=self.pid)
        print('RET: %s' % ret)
        return ApplicationFlag.objects(locked_by_backend=self.backend,
                                       locked_by_pid=self.pid).first()

    def build_package(self, app):
        """
        Build package for application.
        """
        fresh = app.flags.get(ApplicationFlags.build_fresh_package)
        interpreter_version = app.flags.get(ApplicationFlags.needs_building)

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
