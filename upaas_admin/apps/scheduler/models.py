# -*- coding: utf-8 -*-
"""
    :copyright: Copyright 2013 by Łukasz Mierzwa
    :contact: l.mierzwa@gmail.com
"""


from mongoengine import *

from django.utils.translation import ugettext_lazy as _

from upaas_admin.config import cached_main_config


class UserBudget(Document):
    """
    How much resources can user apps consume.
    """
    user = ReferenceField('User', dbref=False)
    apps_count = LongField(required=True,
                           verbose_name=_('application count limit'))
    memory_limit = IntField(required=True,
                            verbose_name=_('memory limit'))
    #TODO add cgroup limits

    _default_manager = QuerySetManager()

    meta = {
        'indexes': [
            {'fields': ['user'], 'unique': True}
        ]
    }

    @classmethod
    def get_default_limits(cls):
        config = cached_main_config()
        return config.dump()['defaults']['budget']


class ApplicationRunPlan(Document):
    """
    Where should application run and how much resources can given app consume.
    """
    application = ReferenceField('Application', dbref=False)
    #FIXME adding reverse_delete_rule=DENY to backends fails, fix it
    backends = ListField(ReferenceField('BackendServer', dbref=False))
    memory_limit = IntField(required=False,
                            verbose_name=_('memory limit'))
    #TODO add cgroup limits

    _default_manager = QuerySetManager()
