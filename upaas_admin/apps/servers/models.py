# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013-2014 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from __future__ import unicode_literals

import datetime
import logging
from random import randrange

from mongoengine import *

from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from upaas.inet import local_ipv4_addresses

from upaas_admin.common.fields import IPv4Field
from upaas_admin.apps.scheduler.models import ApplicationRunPlan


log = logging.getLogger(__name__)


class BackendServer(Document):
    """
    Backend server - used for running applications.
    """
    date_created = DateTimeField(required=True, default=datetime.datetime.now)
    name = StringField(required=True, max_length=128, unique=True,
                       verbose_name=_('name'))
    ip = IPv4Field(required=True, unique=True, verbose_name=_('IP address'))
    is_enabled = BooleanField(default=True, verbose_name=_('enabled'))
    worker_ping = DictField()

    _default_manager = QuerySetManager()

    meta = {
        'indexes': ['name', 'ip', 'is_enabled'],
        'ordering': ['name'],
    }

    @classmethod
    def get_local_backend(cls):
        for local_ip in local_ipv4_addresses():
            backend = cls.objects(ip=local_ip).first()
            if backend:
                return backend

    @property
    def safe_id(self):
        return str(self.id)

    @property
    def run_plans(self):
        """
        Returns the list of application run plans scheduled to be running on
        this backend.
        """
        return ApplicationRunPlan.objects(backends__backend=self)

    @property
    def port_min(self):
        return settings.UPAAS_CONFIG.apps.tcp.port_min

    @property
    def port_max(self):
        return settings.UPAAS_CONFIG.apps.tcp.port_max

    @property
    def allocated_ports(self):
        """
        Returns all port number allocated to apps.
        """

        ports = []
        for run_plan in self.run_plans:
            backend_conf = run_plan.backend_settings(self)
            if backend_conf:
                ports.append(backend_conf.socket)
                ports.append(backend_conf.stats)
            else:
                log.warning(_("Backend {backend} not found in run plan for "
                              "{name}").format(
                            backend=self.name, name=run_plan.application.name))
        return ports

    @property
    def maximum_ports(self):
        return self.port_max - self.port_min

    @property
    def ports_available(self):
        return self.maximum_ports - len(self.allocated_ports)

    @property
    def is_healthy(self):
        if not self.worker_ping:
            return False
        limit = datetime.datetime.now() - datetime.timedelta(seconds=300)
        for timestamp in list(self.worker_ping.values()):
            if timestamp < limit:
                return False
        return True

    def application_settings(self, application):
        return self.run_plans.filter(application=application).first()

    def find_free_ports(self, count):
        """
        Find and return random port number not allocated to any application.
        Return None if no such port can be found.
        """
        ports = []
        if self.ports_available <= 0:
            log.error("No more free port available, used all %d "
                      "ports" % self.maximum_ports)
            return
        while True:
            # TODO random can take very long to find free port if port usage is
            # TODO high, maybe linear search would be better?
            port = randrange(self.port_min, self.port_max+1)
            if port not in self.allocated_ports and port not in ports:
                ports.append(port)
            if len(ports) == count:
                return ports
        return []


class RouterServer(Document):
    """
    Router server - used for load balancing.
    """
    date_created = DateTimeField(required=True, default=datetime.datetime.now)
    name = StringField(required=True, max_length=60, unique=True,
                       verbose_name=_('name'))
    subscription_ip = IPv4Field(
        required=True, unique=True,
        verbose_name=_('subscription listening IP address'))
    subscription_port = IntField(required=True, default=2626, min_value=1,
                                 max_value=65535,
                                 verbose_name=_('subscription port'))
    is_enabled = BooleanField(default=True, verbose_name=_('enabled'))

    _default_manager = QuerySetManager()

    meta = {
        'indexes': ['name', 'subscription_ip', 'is_enabled'],
        'ordering': ['name'],
    }

    @property
    def safe_id(self):
        return str(self.id)
