# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import absolute_import

from socket import gethostname

from celery.signals import worker_ready
from celery.utils.log import get_task_logger

from upaas.inet import local_ipv4_addresses

from upaas_admin.apps.servers.models import BackendServer


log = get_task_logger(__name__)


@worker_ready.connect
def register_local_backend(sender=None, conf=None, **kwargs):
    print((sender, conf, kwargs))
    log.debug("Celery started, registering local backend if needed")

    for local_ip in local_ipv4_addresses():
        log.debug("Looking for backend with IP '%s'" % local_ip)
        backend = BackendServer.objects(ip=local_ip).first()
        if backend:
            return

    name = gethostname()
    log.info("Registering backend as '%s' with IP '%s'" % (name, local_ip))
    backend = BackendServer(name=name, ip=local_ip)
    backend.save()
