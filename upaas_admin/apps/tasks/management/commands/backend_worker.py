# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import logging
from socket import gethostname

from IPy import IP

from upaas.inet import local_ipv4_addresses

from upaas_admin.apps.tasks.base import BackendTask, PackageTask
from upaas_admin.apps.tasks.daemon import DaemonCommand
from upaas_admin.apps.tasks.constants import TaskStatus
from upaas_admin.apps.servers.models import BackendServer


log = logging.getLogger(__name__)


class Command(DaemonCommand):

    help = 'Run backend worker'

    task_class = BackendTask

    def pop_task(self, **kwargs):
        # little magic - BackendTasks are generic but they also cover
        # PackageTask that should be serialized for every application
        # injecting raw mongo query to do so
        running_apps = [t.application for t in PackageTask.objects(
            status=TaskStatus.running, backend=self.backend)]
        return super(Command, self).pop_task(
            backend=self.backend,
            __raw__={'application': {'$nin': [a.id for a in running_apps]}})

    def handle(self, *args, **options):
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
            log.error(u"No IP address found for local backend!")
            return

        if backend:
            local_ips = local_ipv4_addresses()
            if backend.ip not in [IP(ip) for ip in local_ips]:
                local_ip = local_ips[0]
                log.info(u"Updating IP for '%s' from '%s' to '%s'" % (
                    name, backend.ip, local_ip))
                backend.ip = IP(local_ip)
                backend.save()
        else:
            log.info(u"Local backend not found, registering as '%s' with IP "
                     u"'%s'" % (name, local_ip))
            backend = BackendServer(name=name, ip=local_ip)
            backend.save()

        self.backend = backend

        super(Command, self).handle(*args, **options)
