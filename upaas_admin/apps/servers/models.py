# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


import datetime

from mongoengine import *

from django.utils.translation import ugettext_lazy as _

from upaas.inet import local_ipv4_addresses

from upaas_admin.contrib.fields import IPv4Field


class BackendServer(Document):
    """
    Backend server - used for running applications.
    """
    date_created = DateTimeField(required=True, default=datetime.datetime.now)
    name = StringField(required=True, max_length=60, verbose_name=_('name'))
    ip = IPv4Field(required=True, unique=True, verbose_name=_('IP address'))
    is_enabled = BooleanField(default=True, verbose_name=_('enabled'))

    _default_manager = QuerySetManager()

    meta = {
        'indexes': [
            {'fields': ['name', 'ip'], 'unique': True}
        ],
        'ordering': ['name'],
    }

    @classmethod
    def get_local_backend(cls):
        for local_ip in local_ipv4_addresses():
            backend = cls.objects(ip=local_ip).first()
            if backend:
                return backend


class RouterServer(Document):
    """
    Router server - used for load balancing.
    """
    date_created = DateTimeField(required=True, default=datetime.datetime.now)
    name = StringField(required=True, max_length=60, verbose_name=_('name'))
    private_ip = IPv4Field(required=True, unique=True,
                           verbose_name=_('private IP address'))
    public_ip = IPv4Field(required=True, unique=True,
                          verbose_name=_('public IP address'))
    is_enabled = BooleanField(default=True, verbose_name=_('enabled'))

    _default_manager = QuerySetManager()

    meta = {
        'indexes': [
            {'fields': ['name', 'private_ip', 'public_ip'], 'unique': True}
        ],
        'ordering': ['name'],
    }
