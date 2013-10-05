# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import logging
import time
from socket import gethostname

from IPy import IP

from django.core.management.base import BaseCommand

from upaas.inet import local_ipv4_addresses

from upaas_admin.apps.tasks.base import BackendTask
from upaas_admin.apps.servers.models import BackendServer

log = logging.getLogger(__name__)


class Command(BaseCommand):

    help = 'Run backend worker'

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
            log.error(u"Local backend not found, registering as '%s' with IP "
                      u"'%s'" % (name, local_ip))
            backend = BackendServer(name=name, ip=local_ip)
            backend.save()

        while True:
            try:
                task = BackendTask.pop(backend=backend)
                if task:
                    log.info(u"Got %s with id '%s'" % (
                        task.__class__.__name__, task.id))
                    task.execute()
                else:
                    log.debug(u"No task popped, sleeping")
                    time.sleep(2)
            except KeyboardInterrupt:
                log.info(u"Got ctr+c, exiting")
                break
