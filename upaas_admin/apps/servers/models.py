# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import logging
import datetime
from random import randrange

from mongoengine import *

from django.utils.translation import ugettext_lazy as _

from upaas.inet import local_ipv4_addresses

from upaas_admin.config import cached_main_config
from upaas_admin.contrib.fields import IPv4Field
from upaas_admin.apps.scheduler.models import ApplicationRunPlan


log = logging.getLogger(__name__)


class Ports(EmbeddedDocument):
    application = ReferenceField('Application', dbref=False, unique=True)
    ports = DictField()


class BackendServer(Document):
    """
    Backend server - used for running applications.
    """
    date_created = DateTimeField(required=True, default=datetime.datetime.now)
    name = StringField(required=True, max_length=128, unique=True,
                       verbose_name=_('name'))
    ip = IPv4Field(required=True, unique=True, verbose_name=_('IP address'))
    is_enabled = BooleanField(default=True, verbose_name=_('enabled'))
    ports = ListField(EmbeddedDocumentField(Ports))

    _default_manager = QuerySetManager()

    meta = {
        'indexes': ['name', 'ip'],
        'ordering': ['name'],
    }

    @classmethod
    def get_local_backend(cls):
        for local_ip in local_ipv4_addresses():
            backend = cls.objects(ip=local_ip).first()
            if backend:
                return backend

    @property
    def run_plans(self):
        """
        Returns the list of application run plans scheduled to be running on
        this backend.
        """
        return ApplicationRunPlan.objects(backends=self)

    @property
    def port_min(self):
        return cached_main_config().apps.tcp.port_min

    @property
    def port_max(self):
        return cached_main_config().apps.tcp.port_max

    @property
    def allocated_ports(self):
        """
        Returns all port number allocated to apps.
        """
        ports = []
        for ports_data in self.ports:
            ports.extend(ports_data.ports.values())
        return ports

    @property
    def maximum_ports(self):
        return self.port_max - self.port_min

    @property
    def ports_available(self):
        return self.maximum_ports - len(self.allocated_ports)

    def application_ports(self, application):
        for ports_data in self.ports:
            if ports_data.application == application:
                return ports_data

    def find_free_port(self):
        """
        Find and return random port number not allocated to any application.
        Return None if no such port can be found.
        """
        if self.ports_available <= 0:
            log.error(u"No more free port available, used all %d "
                      u"ports" % self.maximum_ports)
            return
        while True:
            #TODO random can take very long to find free port if port usage is
            #TODO high, maybe linear search would be better?
            port = randrange(self.port_min, self.port_max+1)
            if port not in self.allocated_ports:
                return port

    def set_application_ports(self, application, ports):
        """
        Set port mapping for given application on this backend.
        """
        ports_data = self.application_ports(application)
        if ports_data:
            ports_data.ports = ports
        else:
            ports_data = Ports(application=application, ports=ports)
            self.ports.append(ports_data)
        self.save()

    def delete_application_ports(self, application):
        """
        Remove application from this backend port mapping.
        """
        ports_data = self.application_ports(application)
        if ports_data:
            self.ports.remove(ports_data)
            self.save()
            log.info(u"Removed port mapping for '%s' on '%s'" % (
                application.name, self.name))


class RouterServer(Document):
    """
    Router server - used for load balancing.
    """
    date_created = DateTimeField(required=True, default=datetime.datetime.now)
    name = StringField(required=True, max_length=60, unique=True,
                       verbose_name=_('name'))
    private_ip = IPv4Field(required=True, unique=True,
                           verbose_name=_('private IP address'))
    public_ip = IPv4Field(required=True, unique=True,
                          verbose_name=_('public IP address'))
    subscription_port = IntField(required=True, default=2626, min_value=1,
                                 max_value=65535,
                                 verbose_name=_('subscription port'))
    is_enabled = BooleanField(default=True, verbose_name=_('enabled'))

    _default_manager = QuerySetManager()

    meta = {
        'indexes': ['name', 'private_ip', 'public_ip'],
        'ordering': ['name'],
    }
