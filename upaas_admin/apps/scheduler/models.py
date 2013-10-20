# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from mongoengine import *

from django.utils.translation import ugettext_lazy as _
from django.conf import settings


class BudgetLimits(Document):
    worker_limit = IntField(required=True, verbose_name=_('worker limit'))
    memory_limit = IntField(required=True,
                            verbose_name=_('memory limit'))
    #TODO add cgroup limits

    _default_manager = QuerySetManager()

    meta = {
        'abstract': True,
    }


class UserBudget(BudgetLimits):
    """
    How much resources can user apps consume.
    """
    user = ReferenceField('User', dbref=False, unique=True, required=True)
    apps_count = IntField(required=True,
                          verbose_name=_('application count limit'))

    meta = {
        'indexes': ['user'],
    }

    @classmethod
    def get_default_limits(cls):
        return settings.UPAAS_CONFIG.dump()['defaults']['budget']


class ApplicationRunPlan(BudgetLimits):
    """
    Where should application run and how much resources can given app consume.
    """
    application = ReferenceField('Application', dbref=False, required=True)
    #FIXME adding reverse_delete_rule=DENY to backends fails, fix it
    backends = ListField(ReferenceField('BackendServer', dbref=False))

    meta = {
        'indexes': ['application'],
    }
