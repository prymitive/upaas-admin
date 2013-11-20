# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from mongoengine import (Document, QuerySetManager, IntField, ReferenceField,
                         ListField, BooleanField)

from django.utils.translation import ugettext_lazy as _
from django.conf import settings


class UserLimits(Document):
    """
    How much resources can user apps consume.
    """
    user = ReferenceField('User', dbref=False, unique=True, required=True)

    registered_apps = IntField(verbose_name=_('registered application limit'))
    running_apps = IntField(verbose_name=_('running applications limit'))
    packages_per_app = IntField(verbose_name=_('stored packages limit'))

    instances = IntField(verbose_name=_('running instance limit'))
    workers = IntField(verbose_name=_('running workers limit'))
    memory = IntField(verbose_name=_('allocated memory limit'))

    meta = {
        'indexes': ['user'],
    }

    _default_manager = QuerySetManager()

    limit_fields = ['instances', 'workers', 'memory', 'registered_apps',
                    'running_apps', 'packages_per_app']

    @classmethod
    def get_default_limits(cls):
        return settings.UPAAS_CONFIG.dump()['defaults']['limits']


class ApplicationRunPlan(Document):
    """
    Where should application run and how much resources can given app consume.
    """
    application = ReferenceField('Application', dbref=False, required=True,
                                 unique=True)
    #FIXME adding reverse_delete_rule=DENY to backends fails, fix it
    backends = ListField(ReferenceField('BackendServer', dbref=False))

    instances_min = IntField(required=True,
                             verbose_name=_('instances minimum'))
    instances_max = IntField(required=True,
                             verbose_name=_('instances maximum'))
    workers = IntField(required=True, verbose_name=_('running workers limit'))
    memory = IntField(required=True, verbose_name=_('allocated memory limit'))

    _default_manager = QuerySetManager()
