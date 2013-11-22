# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from mongoengine import (Document, QuerySetManager, IntField, ReferenceField,
                         ListField)

from django.utils.translation import ugettext_lazy as _
from django.conf import settings


class UserLimits(Document):
    """
    How much resources can user apps consume.
    """
    user = ReferenceField('User', dbref=False, unique=True, required=True)

    running_apps = IntField(verbose_name=_('running applications limit'))
    packages_per_app = IntField(verbose_name=_('stored packages limit'))

    instances = IntField(verbose_name=_('total running instance limit'))
    workers = IntField(verbose_name=_('total running workers limit'))
    memory = IntField(verbose_name=_('total memory limit'))

    meta = {
        'indexes': ['user'],
    }

    _default_manager = QuerySetManager()

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

    instances_min = IntField(required=True, min_value=1,
                             verbose_name=_('instances minimum'))
    instances_max = IntField(required=True, min_value=1,
                             verbose_name=_('instances maximum'))
    workers_max = IntField(required=True, min_value=1,
                           verbose_name=_('total workers limit'))
    memory_max = IntField(required=True, verbose_name=_('total memory limit'))

    _default_manager = QuerySetManager()
